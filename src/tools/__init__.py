"""Independent commercial data tools intended for future Function Calling."""

from src.tools.customers import buscar_cliente
from src.tools.orders import consultar_itens_pedido, consultar_pedido
from src.tools.products import buscar_produto, consultar_estoque
from src.tools.promotions import consultar_promocao

__all__ = [
    "buscar_cliente",
    "buscar_produto",
    "consultar_estoque",
    "consultar_itens_pedido",
    "consultar_pedido",
    "consultar_promocao",
]
