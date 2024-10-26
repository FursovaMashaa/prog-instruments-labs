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
        self.matchTerm = None
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
        self.customerDataLayer = CustomerDataLayer(db)

    def loadCompanyCustomer(
        self, externalId: str, companyNumber: Optional[str]
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
        matchByExternalId: Customer = (
            self.customerDataLayer.findByMasterExternalId(externalId)
        )

        if matchByExternalId is not None:
            matches.customer = matchByExternalId
            matches.matchTerm = "ExternalId"
            matchByMasterId: Customer = (
                self.customerDataLayer.findByMasterExternalId(externalId)
            )
            if matchByMasterId is not None:
                matches.add_duplicate(matchByMasterId)
        else:
            matchByCompanyNumber: Customer = (
                self.customerDataLayer.findByCompanyNumber(companyNumber)
            )
            if matchByCompanyNumber is not None:
                matches.customer = matchByCompanyNumber
                matches.matchTerm = "CompanyNumber"

        return matches

    def loadPersonCustomer(self, externalId: str) -> CustomerMatches:
        """
        Загружает информацию о личном клиенте по внешнему идентификатору.

        Args:
            externalId (str): Внешний идентификатор клиента.

        Returns:
            CustomerMatches: Объект с информацией о совпадениях клиентов.
        """
        matches = CustomerMatches()
        matchByPersonalNumber: Customer = (
            self.customerDataLayer.findByExternalId(externalId)
        )

        matches.customer = matchByPersonalNumber
        if matchByPersonalNumber is not None:
            matches.matchTerm = "ExternalId"

        return matches

    def updateCustomerRecord(self, customer: Customer) -> None:
        """
        Обновляет запись клиента в базе данных.

        Args:
            customer (Customer): Клиент, чью запись необходимо обновить.
        """
        self.customerDataLayer.updateCustomerRecord(customer)

    def createCustomerRecord(self, customer: Customer) -> Customer:
        """
        Создает новую запись клиента в базе данных.

        Args:
            customer (Customer): Клиент для создания новой записи.

        Returns:
            Customer: Созданная запись клиента.
        """
        return self.customerDataLayer.createCustomerRecord(customer)

    def updateShoppingList(
        self, customer: Customer, shoppingList: ShoppingList
    ) -> None:
        """
        Обновляет список покупок клиента и запись клиента в базе данных.

        Args:
            customer (Customer): Клиент, чей список покупок необходимо обновить.
            shoppingList (ShoppingList): Новый список покупок для обновления.
        """
        customer.addShoppingList(shoppingList)
        self.customerDataLayer.updateShoppingList(shoppingList)
        self.customerDataLayer.updateCustomerRecord(customer)


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

    def findByExternalId(self, externalId: str) -> Optional[Customer]:
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
            (externalId,),
        )
        customer = self._customer_from_sql_select_fields(self.cursor.fetchone())
        return customer

    def _find_addressId(self, customer: Customer) -> Optional[int]:
        """
        Находит идентификатор адреса клиента по внутреннему идентификатору.

        Args:
            customer (Customer): Клиент, для которого необходимо найти адрес.

        Returns:
            Optional[int]: Идентификатор адреса, если найден, иначе None.
        """
        self.cursor.execute(
            "SELECT addressId FROM customers WHERE internalId=?", (customer.internalId,)
        )
        (addressId,) = self.cursor.fetchone()
        if addressId:
            return int(addressId)
        return None

    def _customer_from_sql_select_fields(
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
            internalId=fields[0],
            externalId=fields[1],
            masterExternalId=fields[2],
            name=fields[3],
            customerType=CustomerType(fields[4]),
            companyNumber=fields[5],
        )

        addressId = self._find_addressId(customer)
        if addressId:
            self.cursor.execute(
                "SELECT street, city, postalCode FROM addresses WHERE addressId=?",
                (addressId,),
            )
            addresses = self.cursor.fetchone()
            if addresses:
                (street, city, postalCode) = addresses
                address = Address(street, city, postalCode)
                customer.address = address

        self.cursor.execute(
            "SELECT shoppinglistId FROM customer_shoppinglists WHERE customerId=?",
            (customer.internalId,),
        )
        shoppinglists = self.cursor.fetchall()
        for sl in shoppinglists:
            self.cursor.execute(
                "SELECT products FROM shoppinglists WHERE shoppinglistId=?", (sl[0],)
            )
            products_as_str = self.cursor.fetchone()
            products = products_as_str[0].split(", ")
            customer.addShoppingList(ShoppingList(products))

        return customer

    def findByMasterExternalId(self, masterExternalId: str) -> Optional[Customer]:
        """
        Находит клиента по мастер-внешнему идентификатору.

        Args:
            masterExternalId (str): Мастер-внешний идентификатор клиента.

        Returns:
            Optional[Customer]: Объект клиента, если найден, иначе None.
        """
        self.cursor.execute(
            "SELECT internalId, externalId, masterExternalId, name,"
            "customerType, companyNumber FROM customers WHERE masterExternalId=?",
            (masterExternalId,),
        )
        return self._customer_from_sql_select_fields(self.cursor.fetchone())

    def findByCompanyNumber(self, companyNumber: Optional[str]) -> Optional[Customer]:
        """
        Находит клиента по номеру компании.

        Args:
            companyNumber (Optional[str]): Номер компании клиента.

        Returns:
            Optional[Customer]: Объект клиента, если найден, иначе None.
        """
        self.cursor.execute(
            "SELECT internalId, externalId, masterExternalId, name,"
            "customerType, companyNumber FROM customers WHERE companyNumber=?",
            (companyNumber,),
        )
        return self._customer_from_sql_select_fields(self.cursor.fetchone())

    def createCustomerRecord(self, customer: Customer) -> Customer:
        """
        Создает запись клиента в базе данных и связывает его с адресом и списками покупок.

        Args:
            customer (Customer): Объект клиента, который необходимо сохранить в базе данных.

        Returns:
            Customer: Объект клиента с обновленным внутренним идентификатором.
        """
        customer.internalId = self._nextid("customers")
        self.cursor.execute(
            "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?);",
            (
                customer.internalId,
                customer.externalId,
                customer.masterExternalId,
                customer.name,
                customer.customerType.value,
                customer.companyNumber,
                None,
            ),
        )

        if customer.address:
            addressId = self._nextid("addresses")
            self.cursor.execute(
                "INSERT INTO addresses VALUES (?, ?, ?, ?)",
                (
                    addressId,
                    customer.address.street,
                    customer.address.city,
                    customer.address.postalCode,
                ),
            )
            self.cursor.execute(
                "UPDATE customers SET addressId=? WHERE internalId=?",
                (addressId, customer.internalId),
            )

        if customer.shoppingLists:
            for sl in customer.shoppingLists:
                data = ", ".join(sl)
                self.cursor.execute(
                    "SELECT shoppinglistId FROM shoppinglists WHERE products=?", (data,)
                )
                shoppinglistId = self.cursor.fetchone()
                if not shoppinglistId:
                    shoppinglistId = self._nextid("shoppinglists")
                    self.cursor.execute(
                        "INSERT INTO shoppinglists VALUES (?, ?)",
                        (shoppinglistId, data),
                    )
                self.cursor.execute(
                    "INSERT INTO customer_shoppinglists VALUES (?, ?)",
                    (customer.internalId, shoppinglistId),
                )

        self.conn.commit()
        return customer
    
    def _nextid(self, tablename: str) -> int:
        """
        Получает следующий идентификатор для указанной таблицы, 
        основываясь на максимальном значении ROWID.

        Args:
            tablename (str): Имя таблицы, для которой нужно получить следующий идентификатор.

        Returns:
            int: Следующий доступный идентификатор. Если таблица пуста, возвращает 1.
        """
        self.cursor.execute(f"SELECT MAX(ROWID) AS max_id FROM {tablename};")
        (id,) = self.cursor.fetchone()
        if id:
            return int(id) + 1
        return 1

    def updateCustomerRecord(self, customer: Customer) -> None:
        """
        Обновляет запись клиента в базе данных. При необходимости обновляет адрес и списки покупок.

        Args:
            customer (Customer): Объект клиента с обновленными данными.
        """
        self.cursor.execute(
            "UPDATE customers SET externalId=?, masterExternalId=?, name=?, "
            "customerType=?, companyNumber=? WHERE internalId=?",
            (
                customer.externalId,
                customer.masterExternalId,
                customer.name,
                customer.customerType.value,
                customer.companyNumber,
                customer.internalId,
            ),
        )

        if customer.address:
            addressId = self._find_addressId(customer)
            if not addressId:
                addressId = self._nextid("addresses")
                self.cursor.execute(
                    "INSERT INTO addresses VALUES (?, ?, ?, ?)",
                    (
                        addressId,
                        customer.address.street,
                        customer.address.city,
                        customer.address.postalCode,
                    ),
                )
                self.cursor.execute(
                    "UPDATE customers SET addressId=? WHERE internalId=?",
                    (addressId, customer.internalId),
                )

        self.cursor.execute(
            "DELETE FROM customer_shoppinglists WHERE customerId=?",
            (customer.internalId,),
        )
   
        if customer.shoppingLists:
            for sl in customer.shoppingLists:
                products = ",".join(sl.products)
                self.cursor.execute(
                    "SELECT shoppinglistId FROM shoppinglists WHERE products=?",
                    (products,),
                )
                shoppinglistIds = self.cursor.fetchone()
                if shoppinglistIds is not None:
                    (shoppinglistId,) = shoppinglistIds
                    self.cursor.execute(
                        "INSERT INTO customer_shoppinglists VALUES (?, ?)",
                        (customer.internalId, shoppinglistId),
                    )
                else:
                    shoppinglistId = self._nextid("shoppinglists")
                    self.cursor.execute(
                        "INSERT INTO shoppinglists VALUES (?, ?)",
                        (shoppinglistId, products),
                    )
                    self.cursor.execute(
                        "INSERT INTO customer_shoppinglists VALUES (?, ?)",
                        (customer.internalId, shoppinglistId),
                    )

        self.conn.commit()

    def updateShoppingList(self, shoppingList: ShoppingList) -> None:
        """
        Обновляет запись списка покупок в базе данных.

        Args:
            shoppingList (ShoppingList): Объект списка покупок с обновленными данными.
        """
        pass
