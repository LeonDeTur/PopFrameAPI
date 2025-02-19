from datetime import datetime
from http.client import HTTPException
from pathlib import Path
from typing import Literal

import geopandas as gpd

from iduconfig import Config
from idustorage.storage.storage import Storage
from idugeoserverclient import IduGeoserverClient

from .pickle_cacheable import CacheablePickleObject
from .geoserver_dto import PopFrameGeoserverDTO

class GeoserverStorage:
    """
    Geoserver handling cache and loading layers from api
    """
    def __init__(
            self,
            cache_path: Path,
            config: Config,
    ) -> None:
        """
        Initialisation function gor geoserver storage class
        Args:
            cache_path (Path): Path to the cache file
            config (Config): Config
        """

        self.config = config
        self.storage = Storage(
            cache_path,
            config
        )
        self.geoserver_client = IduGeoserverClient(
            config=config,
        )

    async def save_gdf_to_geoserver(
            self,
            layer: gpd.GeoDataFrame,
            name: str,
            region_id: int,
            layer_type: Literal["cities", "agglomerations"]
    ) -> None:

        created_at = datetime.now()
        frame = CacheablePickleObject(layer)
        filename = self.storage.save(
            frame,
            name,
            ".pickle",
            created_at,
            region_id,
            layer_type,
        )

        geopackage_name = f"{filename.split('.')[0]}.gpkg"
        frame.to_file(str(self.storage.cache_path / geopackage_name))
        try:
            with open(self.storage.cache_path / geopackage_name, "rb") as fin:
                await self.geoserver_client.upload_layer(
                    self.config.get("GEOSERVER_WORKSPACE"),
                    fin,
                    "popframe",
                    created_at,
                    True,
                    None,
                    region_id
                )
        except Exception as e:
            print(e)

    async def get_layer_from_geoserver(
            self,
            region_id: int,
            layer_type: Literal["cities", "agglomerations"]
    ) -> PopFrameGeoserverDTO:
        layer = await self.geoserver_client.get_layers(
            self.config.get("GEOSERVER_WORKSPACE"), "popframe", region_id, layer_type
        )
        if len(layer) > 1:
            raise HTTPException(500, "FOUND_MULTIPLE_LAYERS")
        elif len(layer) == 0:
            raise HTTPException(404, "LAYER_NOT_FOUND")

        target_layer = layer[0]
        split_layer = '.'.join(target_layer.href.split('.')[:-1]).split('/')[2:]
        return PopFrameGeoserverDTO(
            f"http://{split_layer[0]}",
            split_layer[4],
            split_layer[6],
            target_layer.href
        )
