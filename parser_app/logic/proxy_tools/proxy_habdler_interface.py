from typing import List


class ProxyHandlerInterface:

    def get_name(self) -> str:
        raise NotImplemented("panic! implement me!")

    def get_proxy_list(self, port: int = 3128) -> List[str]:
        raise NotImplemented("panic! implement me!")
