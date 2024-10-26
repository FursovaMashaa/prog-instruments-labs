from typing import Optional, Tuple, Any

from model_objects import Address, Customer, CustomerType, ShoppingList


class CustomerMatches:
    """
    Класс для хранения информации о совпадениях клиентов.
    """
    def __init__(self) -> None:
        """
        Инициализация экземпляра класса CustomerMatches.
        """
        self.match_term = None
        self.customer = None
        self.duplicates = []

    def has_duplicates(self) -> bool:
        """
        Проверяет, есть ли дубликаты клиентов.

        Returns:
            bool: True, если дубликаты найдены, иначе False.
        """
        return bool(self.duplicates)

    def add_duplicate(self, duplicate: Customer) -> None:
        """
        Добавляет дубликат клиента в список.

        Args:
            duplicate (Customer): Дубликат клиента для добавления.
        """
        self.duplicates.append(duplicate)


class CustomerDataAccess:
    """
    Класс для доступа к данным клиентов в базе данных.
    """
    def __init__(self, db) -> None:
        """
        Инициализация экземпляра класса CustomerDataAccess.

        Args:
            db: Объект базы данных для доступа к данным клиентов.
        """
        self.customer_data_layer = CustomerDataLayer(db)

    def load_company_customer(
        self, external_id: str, company_number: Optional[str]
    ) -> CustomerMatches:
        """
        Загружает информацию о компании-клиенте по внешнему идентификатору и номеру компании.

        Args:
            externalId (str): Внешний идентификатор клиента.
            companyNumber (Optional[str]): Номер компании (если доступен).

        Returns:
            CustomerMatches: Объект с информацией о совпадениях клиентов.
        """
        matches = CustomerMatches()
        match_by_external_id: Customer = (
            self.customer_data_layer.find_by_master_external_id(external_id)
        )

        if match_by_external_id is not None:
            matches.customer = match_by_external_id
            matches.match_term = "ExternalId"
            match_by_master_id: Customer = (
                self.customer_data_layer.find_by_master_external_id(external_id)
            )
            if match_by_master_id is not None:
                matches.add_duplicate(match_by_master_id)
        else:
            match_by_company_number: Customer = (
                self.customer_data_layer.find_by_company_number(company_number)
            )
            if match_by_company_number is not None:
                matches.customer = match_by_company_number
                matches.match_term = "CompanyNumber"

        return matches

    def load_person_customer(self, external_id: str) -> CustomerMatches:
        """
        Загружает информацию о личном клиенте по внешнему идентификатору.

        Args:
            externalId (str): Внешний идентификатор клиента.

        Returns:
            CustomerMatches: Объект с информацией о совпадениях клиентов.
        """
        matches = CustomerMatches()
        match_by_personal_number: Customer = (
            self.customer_data_layer.find_by_external_id(external_id)
        )

        matches.customer = match_by_personal_number
        if match_by_personal_number is not None:
            matches.match_term = "ExternalId"

        return matches

    def update_customer_record(self, customer: Customer) -> None:
        """
        Обновляет запись клиента в базе данных.

        Args:
            customer (Customer): Клиент, чью запись необходимо обновить.
        """
        self.customer_data_layer.update_customer_record(customer)

    def create_customer_record(self, customer: Customer) -> Customer:
        """
        Создает новую запись клиента в базе данных.

        Args:
            customer (Customer): Клиент для создания новой записи.

        Returns:
            Customer: Созданная запись клиента.
        """
        return self.customer_data_layer.create_customer_record(customer)

    def update_shopping_list(
        self, customer: Customer, shopping_list: ShoppingList
    ) -> None:
        """
        Обновляет список покупок клиента и запись клиента в базе данных.

        Args:
            customer (Customer): Клиент, чей список покупок необходимо обновить.
            shoppingList (ShoppingList): Новый список покупок для обновления.
        """
        customer.add_shopping_list(shopping_list)
        self.customer_data_layer.update_shopping_list(shopping_list)
        self.customer_data_layer.update_customer_record(customer)


class CustomerDataLayer:
    """
    Класс для доступа к данным клиентов в базе данных.

    Attributes:
        conn: Соединение с базой данных.
        cursor: Курсор для выполнения SQL-запросов.
    """

    def __init__(self, conn):
        """
        Инициализация экземпляра класса CustomerDataLayer.

        Args:
            conn: Объект соединения с базой данных.
        """
        self.conn = conn
        self.cursor = self.conn.cursor()

    def find_by_external_id(self, external_id: str) -> Optional[Customer]:
        """
        Находит клиента по внешнему идентификатору.

        Args:
            externalId (str): Внешний идентификатор клиента.

        Returns:
            Optional[Customer]: Объект клиента, если найден, иначе None.
        """
        self.cursor.execute(
            "SELECT internalId, externalId, masterExternalId, name,"
            "customerType, companyNumber FROM customers WHERE externalId=?",
            (external_id,),
        )
        customer = self.customer_from_sql_select_fields(self.cursor.fetchone())
        return customer

    def find_address_id(self, customer: Customer) -> Optional[int]:
        """
        Находит идентификатор адреса клиента по внутреннему идентификатору.

        Args:
            customer (Customer): Клиент, для которого необходимо найти адрес.

        Returns:
            Optional[int]: Идентификатор адреса, если найден, иначе None.
        """
        self.cursor.execute(
            "SELECT addressId FROM customers WHERE internalId=?", (customer.internal_id,)
        )
        (address_id,) = self.cursor.fetchone()
        if address_id:
            return int(address_id)
        return None

    def customer_from_sql_select_fields(
        self, fields: Optional[Tuple[Any]]
    ) -> Optional[Customer]:
        """
        Создает объект клиента из полей SQL-запроса.

        Args:
            fields (Optional[Tuple[Any]]): Поля, полученные из SQL-запроса.

        Returns:
            Optional[Customer]: Объект клиента, если поля не пустые, иначе None.
        """
        if not fields:
            return None

        customer = Customer(
            internal_id=fields[0],
            external_id=fields[1],
            master_external_id=fields[2],
            name=fields[3],
            customer_type=CustomerType(fields[4]),
            company_number=fields[5],
        )

        address_id = self.find_address_id(customer)
        if address_id:
            self.cursor.execute(
                "SELECT street, city, postalCode FROM addresses WHERE addressId=?",
                (address_id,),
            )
            addresses = self.cursor.fetchone()
            if addresses:
                (street, city, postal_code) = addresses
                address = Address(street, city, postal_code)
                customer.address = address

        self.cursor.execute(
            "SELECT shoppinglistId FROM customer_shoppinglists WHERE customerId=?",
            (customer.internal_id,),
        )
        shopping_lists = self.cursor.fetchall()
        for sl in shopping_lists:
            self.cursor.execute(
                "SELECT products FROM shoppinglists WHERE shoppinglistId=?", (sl[0],)
            )
            products_as_str = self.cursor.fetchone()
            products = products_as_str[0].split(", ")
            customer.add_shopping_list(ShoppingList(products))

        return customer

    def find_by_master_external_id(self, master_external_id: str) -> Optional[Customer]:
        """
        Находит клиента по мастер-внешнему идентификатору.

        Args:
            master_external_id (str): Мастер-внешний идентификатор клиента.

        Returns:
            Optional[Customer]: Объект клиента, если найден, иначе None.
        """
        self.cursor.execute(
            "SELECT internalId, externalId, masterExternalId, name,"
            "customerType, companyNumber FROM customers WHERE masterExternalId=?",
            (master_external_id,),
        )
        return self.customer_from_sql_select_fields(self.cursor.fetchone())

    def find_by_company_number(self, company_number: Optional[str]) -> Optional[Customer]:
        """
        Находит клиента по номеру компании.

        Args:
            company_number (Optional[str]): Номер компании клиента.

        Returns:
            Optional[Customer]: Объект клиента, если найден, иначе None.
        """
        self.cursor.execute(
            "SELECT internalId, externalId, masterExternalId, name,"
            "customerType, companyNumber FROM customers WHERE companyNumber=?",
            (company_number,),
        )
        return self.customer_from_sql_select_fields(self.cursor.fetchone())

    def create_customer_record(self, customer: Customer) -> Customer:
        """
        Создает запись клиента в базе данных и связывает его с адресом и списками покупок.

        Args:
            customer (Customer): Объект клиента, который необходимо сохранить в базе данных.

        Returns:
            Customer: Объект клиента с обновленным внутренним идентификатором.
        """
        customer.internal_id = self.next_id("customers")
        self.cursor.execute(
            "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?);",
            (
                customer.internal_id,
                customer.external_id,
                customer.master_external_id,
                customer.name,
                customer.customer_type.value,
                customer.company_number,
                None,
            ),
        )

        if customer.address:
            address_id = self.next_id("addresses")
            self.cursor.execute(
                "INSERT INTO addresses VALUES (?, ?, ?, ?)",
                (
                    address_id,
                    customer.address.street,
                    customer.address.city,
                    customer.address.postal_code,
                ),
            )
            self.cursor.execute(
                "UPDATE customers SET addressId=? WHERE internalId=?",
                (address_id, customer.internal_id),
            )

        if customer.shopping_lists:
            for sl in customer.shopping_lists:
                data = ", ".join(sl)
                self.cursor.execute(
                    "SELECT shoppinglistId FROM shoppinglists WHERE products=?", (data,)
                )
                shopping_list_id = self.cursor.fetchone()
                if not shopping_list_id:
                    shopping_list_id = self.next_id("shoppinglists")
                    self.cursor.execute(
                        "INSERT INTO shoppinglists VALUES (?, ?)",
                        (shopping_list_id, data),
                    )
                self.cursor.execute(
                    "INSERT INTO customer_shoppinglists VALUES (?, ?)",
                    (customer.internal_id, shopping_list_id),
                )

        self.conn.commit()
        return customer

    def next_id(self, table_name: str) -> int:
        """
        Получает следующий идентификатор для указанной таблицы, 
        основываясь на максимальном значении ROWID.

        Args:
            table_name (str): Имя таблицы, для которой нужно получить следующий идентификатор.

        Returns:
            int: Следующий доступный идентификатор. Если таблица пуста, возвращает 1.
        """
        self.cursor.execute(f"SELECT MAX(ROWID) AS max_id FROM {table_name};")
        (max_id,) = self.cursor.fetchone()
        if max_id:
            return int(max_id) + 1
        return 1

    def update_customer_record(self, customer: Customer) -> None:
        """
        Обновляет запись клиента в базе данных. При необходимости обновляет адрес и списки покупок.

        Args:
            customer (Customer): Объект клиента с обновленными данными.
        """
        self.cursor.execute(
            "UPDATE customers SET externalId=?, masterExternalId=?, name=?, "
            "customerType=?, companyNumber=? WHERE internalId=?",
            (
                customer.external_id,
                customer.master_external_id,
                customer.name,
                customer.customer_type.value,
                customer.company_number,
                customer.internal_id,
            ),
        )

        if customer.address:
            address_id = self.find_address_id(customer)
            if not address_id:
                address_id = self.next_id("addresses")
                self.cursor.execute(
                    "INSERT INTO addresses VALUES (?, ?, ?, ?)",
                    (
                        address_id,
                        customer.address.street,
                        customer.address.city,
                        customer.address.postal_code,
                    ),
                )
                self.cursor.execute(
                    "UPDATE customers SET addressId=? WHERE internalId=?",
                    (address_id, customer.internal_id),
                )

        self.cursor.execute(
            "DELETE FROM customer_shoppinglists WHERE customerId=?",
            (customer.internal_id,),
        )

        if customer.shopping_lists:
            for sl in customer.shopping_lists:
                products = ",".join(sl.products)
                self.cursor.execute(
                    "SELECT shoppinglistId FROM shoppinglists WHERE products=?",
                    (products,),
                )
                shopping_list_ids = self.cursor.fetchone()
                if shopping_list_ids is not None:
                    (shopping_list_id,) = shopping_list_ids
                    self.cursor.execute(
                        "INSERT INTO customer_shoppinglists VALUES (?, ?)",
                        (customer.internal_id, shopping_list_id),
                    )
                else:
                    shopping_list_id = self.next_id("shoppinglists")
                    self.cursor.execute(
                        "INSERT INTO shoppinglists VALUES (?, ?)",
                        (shopping_list_id, products),
                    )
                    self.cursor.execute(
                        "INSERT INTO customer_shoppinglists VALUES (?, ?)",
                        (customer.internal_id, shopping_list_id),
                    )

        self.conn.commit()

    def update_shopping_list(self, shopping_list: ShoppingList) -> None:
        """
        Обновляет запись списка покупок в базе данных.

        Args:
            shoppingList (ShoppingList): Объект списка покупок с обновленными данными.
        """
        pass
