from geoalchemy2.elements import WKBElement, WKTElement
from geoalchemy2.shape import to_shape
from shapely import from_wkt
from shapely.geometry import box, Polygon
from pydantic import BaseModel, Field

class Extent(BaseModel):
    """Pydantic model for a geographic extent.

    An extent is a rectangular bounding box in 2 dimensions.
    """
    longitude_min: float = Field(
        ge=-180.0,
        le=180.0,
        description="Mininum Longitude, in degrees, defining the boundary"
    )
    latitude_min: float = Field(
        ge=-90.0,
        le=90.0,
        description="Mininum Latitude, in degrees, defining the boundary"
    )
    longitude_max: float = Field(
        ge=-180.0,
        le=180.0,
        description="Maximim Longitude, in degrees, defining the boundary"
    )
    latitude_max: float = Field(
        ge=-90.0,
        le=90.0,
        description="Maximum Latitude, in degrees, defining the boundary"
    )

    def to_wkt(self) -> str:
        """Converts the extent to a WKT string"""
        return box(
            self.longitude_min,
            self.latitude_min,
            self.longitude_max,
            self.latitude_max
        ).wkt

    @classmethod
    def from_wkt(cls, wkt: str):
        """Constructs an Extent from a WKT string"""
        shape = from_wkt(wkt)
        if isinstance(shape, Polygon):
            return cls.from_shapely_polygon(shape)

        raise ValueError(wkt)

    @classmethod
    def from_geoalchemy_element(cls, geom: WKBElement | WKTElement):
        """Constructs an Extent from a GeoAlchemy2 WKTElement or WKBElement"""
        shape = to_shape(geom)
        if isinstance(shape, Polygon):
            return cls.from_shapely_polygon(shape)

        raise ValueError(geom)

    @classmethod
    def from_shapely_polygon(cls, polygon: Polygon):
        """Constructs an Extent from a Shapely Polygon"""
        # there are probably more efficient comparisons, but this works
        if box(*polygon.bounds).equals(polygon):
            return cls(
                longitude_min=polygon.bounds[0],
                latitude_min=polygon.bounds[1],
                longitude_max=polygon.bounds[2],
                latitude_max=polygon.bounds[3]
            )

        raise ValueError(polygon, "The shape is not a bounding box")


def convert_geoalchemy_element(point: any) -> any:
    """Pre Validator used by Pydantic to convert GeoAlchemy2 elements to Extent"""
    if isinstance(point, (WKBElement, WKTElement)):
        return Extent.from_geoalchemy_element(point)
    else:
        # let pydantic handle other types
        return point
