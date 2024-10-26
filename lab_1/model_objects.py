from dataclasses import dataclass, field
from typing import List, Optional

from enum import Enum

from dataclasses_json import dataclass_json


class CustomerType(Enum):
    """Перечисление, представляющее тип клиента."""
    PERSON = 1
    COMPANY = 2 


@dataclass_json
@dataclass
class ShoppingList:
    """Класс, представляющий список покупок.

    Args:
        products (List[str]): Список названий продуктов в списке покупок.
    """
    products: List[str] = field(default_factory=list)


@dataclass_json
@dataclass(frozen=True)
class Address:
    """Класс, представляющий почтовый адрес.

    Args:
        street (str): Улица адреса.
        city (str): Город адреса.
        postalCode (str): Почтовый индекс адреса.
    """
    street: str
    city: str
    postalCode: str


@dataclass_json
@dataclass(frozen=True)
class ExternalCustomer:
    """Класс, представляющий внешнего клиента.

    Args:
        externalId (str): Уникальный идентификатор внешнего клиента.
        name (str): Имя клиента.
        isCompany (bool): Указывает, является ли клиент компанией.
        companyNumber (Optional[str]): Регистрационный номер компании, если применимо.
        preferredStore (str): Предпочитаемый магазин клиента.
        postalAddress (Address): Почтовый адрес клиента.
        shoppingLists (List[ShoppingList]): Список списков покупок, связанных с клиентом.
    """
    externalId: str
    name: str
    isCompany: bool
    companyNumber: Optional[str]
    preferredStore: str
    postalAddress: Address
    shoppingLists: List[ShoppingList] = field(default_factory=list)


class Customer:
    """Класс, представляющий клиента с внутренними и внешними идентификаторами.

    Args:
        internalId (Optional[str]): Уникальный идентификатор внутреннего клиента.
        externalId (Optional[str]): Уникальный идентификатор внешнего клиента.
        masterExternalId (Optional[str]): Основной идентификатор для связанных внешних клиентов.
        name (Optional[str]): Имя клиента.
        customerType (Optional[CustomerType]): Тип клиента (индивидуальный или компания).
        companyNumber (Optional[str]): Регистрационный номер компании, если применимо.
        shoppingLists (List[ShoppingList]): Список списков покупок, связанных с клиентом.
        address (Optional[Address]): Почтовый адрес клиента.
    """

    def __init__(
            self,
            internalId: str = None,
            externalId: str = None,
            masterExternalId: str = None,
            name: str = None,
            customerType: CustomerType = None,
            companyNumber: str = None
    ):
        self.internalId = internalId
        self.externalId = externalId
        self.masterExternalId = masterExternalId
        self.name = name
        self.customerType = customerType
        self.companyNumber = companyNumber
        self.shoppingLists = []
        self.address = None

    def addShoppingList(self, shoppingList: ShoppingList) -> None:
        """Добавляет список покупок в коллекцию списков покупок клиента.

        Args:
            shoppingList (ShoppingList): Список покупок, который нужно добавить.
        """
        self.shoppingLists.append(shoppingList)