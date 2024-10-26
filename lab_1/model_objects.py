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
    postal_code: str


@dataclass_json
@dataclass(frozen=True)
class ExternalCustomer:
    """Класс, представляющий внешнего клиента.

    Args:
        external_id (str): Уникальный идентификатор внешнего клиента.
        name (str): Имя клиента.
        is_company (bool): Указывает, является ли клиент компанией.
        company_number (Optional[str]): Регистрационный номер компании, если применимо.
        preferred_store (str): Предпочитаемый магазин клиента.
        postal_address (Address): Почтовый адрес клиента.
        shopping_lists (List[ShoppingList]): Список списков покупок, связанных с клиентом.
    """
    external_id: str
    name: str
    is_company: bool
    company_number: Optional[str]
    preferred_store: str
    postal_address: Address
    shopping_lists: List[ShoppingList] = field(default_factory=list)


class Customer:
    """Класс, представляющий клиента с внутренними и внешними идентификаторами.

    Args:
        internal_id (Optional[str]): Уникальный идентификатор внутреннего клиента.
        external_id (Optional[str]): Уникальный идентификатор внешнего клиента.
        master_external_id (Optional[str]): Основной идентификатор для связанных внешних клиентов.
        name (Optional[str]): Имя клиента.
        customer_type (Optional[CustomerType]): Тип клиента (индивидуальный или компания).
        company_number (Optional[str]): Регистрационный номер компании, если применимо.
        shopping_lists (List[ShoppingList]): Список списков покупок, связанных с клиентом.
        address (Optional[Address]): Почтовый адрес клиента.
    """

    def __init__(
            self,
            internal_id: str = None,
            external_id: str = None,
            master_external_id: str = None,
            name: str = None,
            customer_type: CustomerType = None,
            company_number: str = None
    ):
        self.internal_id = internal_id
        self.external_id = external_id
        self.master_external_id = master_external_id
        self.name = name
        self.customer_type = customer_type
        self.company_number = company_number
        self.shopping_lists = []
        self.address = None

    def add_shopping_list(self, shopping_list: ShoppingList) -> None:
        """Добавляет список покупок в коллекцию списков покупок клиента.

        Args:
            shopping_list (ShoppingList): Список покупок, который нужно добавить.
        """
        self.shopping_lists.append(shopping_list)
