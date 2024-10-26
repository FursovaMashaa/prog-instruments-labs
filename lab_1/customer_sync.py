from typing import Optional

from customer_data_access import CustomerMatches
from model_objects import Customer, CustomerType, ExternalCustomer


class ConflictException(Exception):
    """Исключение, возникающее при конфликте данных."""
    pass


class CustomerSync:
    def __init__(self, customerDataAccess) -> None:
        """
        Инициализирует экземпляр класса CustomerSync.

        Args:
            customerDataAccess: Объект доступа к данным клиентов, 
            используемый для взаимодействия с базой данных.
        """
        self.customerDataAccess = customerDataAccess

    def syncWithDataLayer(self, externalCustomer: ExternalCustomer) -> bool:
        """
        Синхронизирует данные клиента с внешним источником данных.

        Args:
            externalCustomer (ExternalCustomer): Объект внешнего 
            клиента, содержащий данные для синхронизации.

        Returns:
            bool: True, если был создан новый клиент, иначе False.
        """
        customerMatches: CustomerMatches
        if externalCustomer.isCompany:
            customerMatches = self.loadCompany(externalCustomer)
        else:
            customerMatches = self.loadPerson(externalCustomer)

        customer = customerMatches.customer

        if customer is None:
            customer = Customer()
            customer.externalId = externalCustomer.externalId
            customer.masterExternalId = externalCustomer.externalId

        self.populateFields(externalCustomer, customer)

        created = False
        if customer.internalId is None:
            customer = self.createCustomer(customer)
            created = True
        else:
            self.updateCustomer(customer)

        self.updateContactInfo(externalCustomer, customer)

        if customerMatches.has_duplicates:
            for duplicate in customerMatches.duplicates:
                self.updateDuplicate(externalCustomer, duplicate)

        self.updateRelations(externalCustomer, customer)
        self.updatePreferredStore(externalCustomer, customer)

        return created

    def updateRelations(self, externalCustomer: ExternalCustomer, customer: Customer) -> None:
        """
        Обновляет связи клиента с его списками покупок.

        Args:
            externalCustomer (ExternalCustomer): Объект внешнего клиента.
            customer (Customer): Объект клиента, данные которого обновляются.
        """
        consumerShoppingLists = externalCustomer.shoppingLists
        for consumerShoppingList in consumerShoppingLists:
            self.customerDataAccess.updateShoppingList(customer, consumerShoppingList)

    def updateCustomer(self, customer: Customer) -> Customer:
        """
        Обновляет запись клиента в базе данных.

        Args:
            customer (Customer): Объект клиента с обновленными данными.

        Returns:
            Customer: Обновленный объект клиента.
        """
        return self.customerDataAccess.updateCustomerRecord(customer)

    def updateDuplicate(
            self,
            externalCustomer: ExternalCustomer,
            duplicate: Optional[Customer]
    ) -> None:
        """
        Обновляет запись дублирующего клиента.

        Args:
            externalCustomer (ExternalCustomer): Объект внешнего клиента.
            duplicate (Optional[Customer]): Объект дублирующего клиента. 
            Если None, создается новый объект.
        """
        if duplicate is None:
            duplicate = Customer()
            duplicate.externalId = externalCustomer.externalId
            duplicate.masterExternalId = externalCustomer.externalId

        duplicate.name = externalCustomer.name

        if duplicate.internalId is None:
            self.createCustomer(duplicate)
        else:
            self.updateCustomer(duplicate)

    def updatePreferredStore(
            self,
            externalCustomer: ExternalCustomer,
            customer: Customer
    ) -> None:
        """
        Обновляет предпочтительный магазин клиента.

        Args:
            externalCustomer (ExternalCustomer): Объект внешнего клиента.
            customer (Customer): Объект клиента, данные которого обновляются.
        """
        customer.preferredStore = externalCustomer.preferredStore

    def createCustomer(self, customer: Customer) -> Customer:
        """
        Создает новую запись клиента в базе данных.

        Args:
            customer (Customer): Объект нового клиента.

        Returns:
            Customer: Созданный объект клиента.
        """
        return self.customerDataAccess.createCustomerRecord(customer)

    def populateFields(
            self,
            externalCustomer: ExternalCustomer,
            customer: Customer
        ) -> None:
        """
        Заполняет поля объекта клиента данными из внешнего источника.

        Args:
            externalCustomer (ExternalCustomer): Объект внешнего клиента.
            customer (Customer): Объект клиента, который нужно заполнить данными.
        """
        customer.name = externalCustomer.name
        if externalCustomer.isCompany:
            customer.companyNumber = externalCustomer.companyNumber
            customer.customerType = CustomerType.COMPANY
        else:
            customer.customerType = CustomerType.PERSON

    def updateContactInfo(
            self,
            externalCustomer: ExternalCustomer,
            customer: Customer
    ) -> None:
        """
        Обновляет контактную информацию клиента.

        Args:
            externalCustomer (ExternalCustomer): Объект внешнего клиента.
            customer (Customer): Объект клиента, данные которого обновляются.
        """
        customer.address = externalCustomer.postalAddress

    def loadCompany(
        self,
        externalCustomer: ExternalCustomer
    ) -> CustomerMatches:
        """
        Загружает информацию о компании-клиенте из базы данных.

        Args:
            externalCustomer (ExternalCustomer): Объект внешнего клиента, 
            содержащий данные о компании.

        Raises:
            ConflictException: Если уже существует клиент с данным внешним идентификатором, 
                            но он не является компанией, или если внешний идентификатор 
                            не совпадает с загруженным номером компании.

        Returns:
            CustomerMatches: Объект, содержащий информацию о найденных клиентах и их совпадениях.
        """
        externalId = externalCustomer.externalId
        companyNumber = externalCustomer.companyNumber

        customerMatches = self.customerDataAccess.loadCompanyCustomer(
            externalId, companyNumber
        )

        if (customerMatches.customer is not None and
                CustomerType.COMPANY != customerMatches.customer.customerType):
            raise ConflictException(
                f"Existing customer for externalCustomer {externalId} "
                "already exists and is not a company"
            )

        if "ExternalId" == customerMatches.matchTerm:
            customerCompanyNumber = customerMatches.customer.companyNumber
            if companyNumber != customerCompanyNumber:
                customerMatches.customer.masterExternalId = None
                customerMatches.add_duplicate(customerMatches.customer)
                customerMatches.customer = None
                customerMatches.matchTerm = None

        elif "CompanyNumber" == customerMatches.matchTerm:
            customerExternalId = customerMatches.customer.externalId
            if (customerExternalId is not None and
                    externalId != customerExternalId):
                raise ConflictException(
                    f"Existing customer for externalCustomer {companyNumber} "
                    f"doesn't match external id {externalId} instead found "
                    f"{customerExternalId}"
                )

            customer = customerMatches.customer
            customer.externalId = externalId
            customer.masterExternalId = externalId
            customerMatches.addDuplicate(None)

        return customerMatches

    def loadPerson(
            self, externalCustomer: ExternalCustomer
    ) -> CustomerMatches:
        """
        Загружает информацию о физическом лице-клиенте из базы данных.

        Args:
            externalCustomer (ExternalCustomer): Объект внешнего клиента, 
            содержащий данные о физическом лице.

        Raises:
            ConflictException: Если уже существует клиент с данным внешним идентификатором, 
                            но он не является физическим лицом.

        Returns:
            CustomerMatches: Объект, содержащий информацию о найденных клиентах и их совпадениях.
        """
        externalId = externalCustomer.externalId
        customerMatches = self.customerDataAccess.loadPersonCustomer(
            externalId
        )

        if customerMatches.customer is not None:
            if CustomerType.PERSON != customerMatches.customer.customerType:
                raise ConflictException(
                    f"Existing customer for externalCustomer {externalId} "
                    "already exists and is not a person"
                )

            if "ExternalId" != customerMatches.matchTerm:
                customer = customerMatches.customer
                customer.externalId = externalId
                customer.masterExternalId = externalId

        return customerMatches
