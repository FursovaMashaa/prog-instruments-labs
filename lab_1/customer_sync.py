from typing import Optional

from customer_data_access import CustomerMatches
from model_objects import Customer, CustomerType, ExternalCustomer


class ConflictException(Exception):
    """Исключение, возникающее при конфликте данных."""
    pass


class CustomerSync:
    def __init__(self, customer_data_access) -> None:
        """
        Инициализирует экземпляр класса CustomerSync.

        Args:
            customer_data_access: Объект доступа к данным клиентов, 
            используемый для взаимодействия с базой данных.
        """
        self.customer_data_access = customer_data_access

    def sync_with_data_layer(self, external_customer: ExternalCustomer) -> bool:
        """
        Синхронизирует данные клиента с внешним источником данных.

        Args:
            external_customer (ExternalCustomer): Объект внешнего 
            клиента, содержащий данные для синхронизации.

        Returns:
            bool: True, если был создан новый клиент, иначе False.
        """
        customer_matches: CustomerMatches
        if external_customer.is_company:
            customer_matches = self.load_company(external_customer)
        else:
            customer_matches = self.load_person(external_customer)

        customer = customer_matches.customer

        if customer is None:
            customer = Customer()
            customer.external_id = external_customer.external_id
            customer.master_external_id = external_customer.external_id

        self.populate_fields(external_customer, customer)

        created = False
        if customer.internal_id is None:
            customer = self.create_customer(customer)
            created = True
        else:
            self.update_customer(customer)

        self.update_contact_info(external_customer, customer)

        if customer_matches.has_duplicates:
            for duplicate in customer_matches.duplicates:
                self.update_duplicate(external_customer, duplicate)

        self.update_relations(external_customer, customer)
        self.update_preferred_store(external_customer, customer)

        return created

    def update_relations(self, external_customer: ExternalCustomer, customer: Customer) -> None:
        """
        Обновляет связи клиента с его списками покупок.

        Args:
            external_customer (ExternalCustomer): Объект внешнего клиента.
            customer (Customer): Объект клиента, данные которого обновляются.
        """
        consumer_shopping_lists = external_customer.shopping_lists
        for consumer_shopping_list in consumer_shopping_lists:
            self.customer_data_access.update_shopping_list(customer, consumer_shopping_list)

    def update_customer(self, customer: Customer) -> Customer:
        """
        Обновляет запись клиента в базе данных.

        Args:
            customer (Customer): Объект клиента с обновленными данными.

        Returns:
            Customer: Обновленный объект клиента.
        """
        return self.customer_data_access.update_customer_record(customer)

    def update_duplicate(
            self,
            external_customer: ExternalCustomer,
            duplicate: Optional[Customer]
    ) -> None:
        """
        Обновляет запись дублирующего клиента.

        Args:
            external_customer (ExternalCustomer): Объект внешнего клиента.
            duplicate (Optional[Customer]): Объект дублирующего клиента. 
            Если None, создается новый объект.
        """
        if duplicate is None:
            duplicate = Customer()
            duplicate.external_id = external_customer.external_id
            duplicate.master_external_id = external_customer.external_id

        duplicate.name = external_customer.name

        if duplicate.internal_id is None:
            self.create_customer(duplicate)
        else:
            self.update_customer(duplicate)

    def update_preferred_store(
            self,
            external_customer: ExternalCustomer,
            customer: Customer
    ) -> None:
        """
        Обновляет предпочтительный магазин клиента.

        Args:
            external_customer (ExternalCustomer): Объект внешнего клиента.
            customer (Customer): Объект клиента, данные которого обновляются.
        """
        customer.preferred_store = external_customer.preferred_store

    def create_customer(self, customer: Customer) -> Customer:
        """
        Создает новую запись клиента в базе данных.

        Args:
            customer (Customer): Объект нового клиента.

        Returns:
            Customer: Созданный объект клиента.
        """
        return self.customer_data_access.create_customer_record(customer)

    def populate_fields(
            self,
            external_customer: ExternalCustomer,
            customer: Customer
        ) -> None:
        """
        Заполняет поля объекта клиента данными из внешнего источника.

        Args:
            external_customer (ExternalCustomer): Объект внешнего клиента.
            customer (Customer): Объект клиента, который нужно заполнить данными.
        """
        customer.name = external_customer.name
        if external_customer.is_company:
            customer.company_number = external_customer.company_number
            customer.customer_type = CustomerType.COMPANY
        else:
            customer.customer_type = CustomerType.PERSON

    def update_contact_info(
            self,
            external_customer: ExternalCustomer,
            customer: Customer
    ) -> None:
        """
        Обновляет контактную информацию клиента.

        Args:
            external_customer (ExternalCustomer): Объект внешнего клиента.
            customer (Customer): Объект клиента, данные которого обновляются.
        """
        customer.address = external_customer.postalAddress

    def load_company(
        self,
        external_customer: ExternalCustomer
    ) -> CustomerMatches:
        """
        Загружает информацию о компании-клиенте из базы данных.

        Args:
            external_customer (ExternalCustomer): Объект внешнего клиента, 
            содержащий данные о компании.

        Returns:
            CustomerMatches: Объект, содержащий информацию о найденных клиентах и их совпадениях.
        """
        external_id = external_customer.external_id
        company_number = external_customer.company_number

        customer_matches = self.customer_data_access.load_company_customer(
            external_id, company_number
        )

        if (customer_matches.customer is not None and
                CustomerType.COMPANY != customer_matches.customer.customer_type):
            raise ConflictException(
                f"Existing customer for externalCustomer {external_id} "
                "already exists and is not a company"
            )

        if "ExternalId" == customer_matches.match_term:
            customer_company_number = customer_matches.customer.company_number
            if company_number != customer_company_number:
                customer_matches.customer.master_external_id = None
                customer_matches.add_duplicate(customer_matches.customer)
                customer_matches.customer = None
                customer_matches.match_term = None

        elif "CompanyNumber" == customer_matches.match_term:
            customer_external_id = customer_matches.customer.external_id
            if (customer_external_id is not None and
                    external_id != customer_external_id):
                raise ConflictException(
                    f"Existing customer for externalCustomer {company_number} "
                    f"doesn't match external id {external_id} instead found "
                    f"{customer_external_id}"
                )

            customer = customer_matches.customer
            customer.external_id = external_id
            customer.master_external_id = external_id
            customer_matches.add_duplicate(None)

        return customer_matches

    def load_person(
            self, external_customer: ExternalCustomer
    ) -> CustomerMatches:
        """
        Загружает информацию о физическом лице-клиенте из базы данных.

        Args:
            external_customer (ExternalCustomer): Объект внешнего клиента, 
            содержащий данные о физическом лице.

        Returns:
            CustomerMatches: Объект, содержащий информацию о найденных клиентах и их совпадениях.
        """
        external_id = external_customer.external_id
        customer_matches = self.customer_data_access.load_person_customer(
            external_id
        )

        if customer_matches.customer is not None:
            if CustomerType.PERSON != customer_matches.customer.customer_type:
                raise ConflictException(
                    f"Existing customer for externalCustomer {external_id} "
                    "already exists and is not a person"
                )

            if "ExternalId" != customer_matches.match_term:
                customer = customer_matches.customer
                customer.external_id = external_id
                customer.master_external_id = external_id

        return customer_matches
