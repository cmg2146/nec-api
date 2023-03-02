from geoalchemy2.elements import WKBElement, WKTElement
from geoalchemy2.shape import to_shape
from shapely import from_wkt
from shapely.geometry import Point
from pydantic import BaseModel, Field

class Coordinates(BaseModel):
    """Schema model for a geographic point"""
    longitude: float = Field(
        ge=-180.0,
        le=180.0,
        description="Longitude in degrees",
        example=0.0
    )
    latitude: float = Field(
        ge=-90.0,
        le=90.0,
        description="Latitude in degrees",
        example=0.0
    )

    def to_wkt(self) -> str:
        """Converts the coordinates to a WKT string"""
        return Point(self.longitude, self.latitude).wkt

    @classmethod
    def from_wkt(cls, wkt: str):
        """Constructs a Coordinates object from a WKT string"""
        shape = from_wkt(wkt)
        if isinstance(shape, Point):
            return cls.from_shapely_point(shape)

        raise ValueError(wkt)

    @classmethod
    def from_geoalchemy_element(cls, geom: WKBElement | WKTElement):
        """Constructs a Coordinates object from a GeoAlchemy2 WKTElement or WKBElement"""
        shape = to_shape(geom)
        if isinstance(shape, Point):
            return cls.from_shapely_point(shape)

        raise ValueError(geom)

    @classmethod
    def from_shapely_point(cls, point: Point):
        """Constructs a Coordinates object from a Shapely Point"""
        return cls(longitude=point.x, latitude=point.y)

def convert_geoalchemy_element(point: any) -> any:
    """Pre Validator used by Pydantic to convert GeoAlchemy2 elements to Coordinates"""
    if isinstance(point, (WKBElement, WKTElement)):
        return Coordinates.from_geoalchemy_element(point)
    else:
        # let pydantic handle other types
        return point
