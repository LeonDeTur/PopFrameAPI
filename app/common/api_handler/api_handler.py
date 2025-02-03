import aiohttp

from app.common.exceptions.http_exception_wrapper import http_exception


class APIHandler:

    def __init__(
            self,
            base_url: str,
    ) -> None:
        """Initialisation function

        Args:
            base_url (str): Base api url
        Returns:
            None
        """

        self.base_url = base_url

    @staticmethod
    async def _check_response_status(
            response: aiohttp.ClientResponse
    ) -> list | dict:
        """Function handles response

        Args:
            response (aiohttp.ClientResponse): Response object
        Returns:
            list|dict: requested data
        Raises:
            http_exception with response status code from API
        """

        if response.status in (200, 201):
            return await response.json()
        elif response.status == 500:
            raise http_exception(
                response.status,
                "Couldn't get data from API",
                _input=response.url,
                _detail=response.text,
            )
        else:
            raise http_exception(
                response.status,
                "Couldn't get data from API",
                _input=response.url.__str__(),
                _detail=await response.json(),
            )

    async def get(
            self,
            endpoint_url: str,
            headers: dict | None = None,
            params: dict | None = None,
            session: aiohttp.ClientSession | None = None,
    ) -> dict | list:
        """Function to get data from api

        Args:
            endpoint_url (str): Endpoint url
            headers (dict | None): Headers
            params (dict | None): Query parameters
            session (aiohttp.ClientSession | None): Session to use
        Returns:
            dict | list: Response data as python object
        """

        if not session:
            session = aiohttp.ClientSession()
        url = self.base_url + endpoint_url
        async with session.get(
                url=url,
                headers=headers,
                params=params
        ) as response:
            result = await self._check_response_status(response)
            return result

    async def post(
            self,
            endpoint_url: str,
            headers: dict | None = None,
            params: dict | None = None,
            data: dict | None = None,
            session: aiohttp.ClientSession | None = None,
        ) -> dict | list:
        """Function to post data from api

        Args:
            endpoint_url (str): Endpoint url
            headers (dict | None): Headers
            params (dict | None): Query parameters
            data (dict | None): Request data
            session (aiohttp.ClientSession | None): Session to use
        Returns:
            dict | list: Response data as python object
        """

        if not session:
            session = aiohttp.ClientSession()
        url = self.base_url + endpoint_url
        with session.post(
            url=url,
            headers=headers,
            params=params,
            data=data,
        ) as response:
            result = await self._check_response_status(response)
            return result

    async def put(
            self,
            endpoint_url: str,
            headers: dict | None = None,
            params: dict | None = None,
            data: dict | None = None,
            session: aiohttp.ClientSession | None = None,
    ) -> dict | list:
        """Function to post data from api

        Args:
            endpoint_url (str): Endpoint url
            headers (dict | None): Headers
            params (dict | None): Query parameters
            data (dict | None): Request data
            session (aiohttp.ClientSession | None): Session to use
        Returns:
            dict | list: Response data as python object
        """

        if not session:
            session = aiohttp.ClientSession()
        url = self.base_url + endpoint_url
        with session.put(
                url=url,
                headers=headers,
                params=params,
                data=data,
        ) as response:
            result = await self._check_response_status(response)
            return result

    async def delete(
            self,
            endpoint_url: str,
            headers: dict | None = None,
            params: dict | None = None,
            data: dict | None = None,
            session: aiohttp.ClientSession | None = None,
    ) -> dict | list:
        """Function to post data from api

        Args:
            endpoint_url (str): Endpoint url
            headers (dict | None): Headers
            params (dict | None): Query parameters
            data (dict | None): Request data
            session (aiohttp.ClientSession | None): Session to use
        Returns:
            dict | list: Response data as python object
        """

        if not session:
            session = aiohttp.ClientSession()
        url = self.base_url + endpoint_url
        with session.delete(
                url=url,
                headers=headers,
                params=params,
                data=data,
        ) as response:
            result = await self._check_response_status(response)
            return result
