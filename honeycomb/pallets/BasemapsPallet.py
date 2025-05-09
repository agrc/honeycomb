from pathlib import Path

from forklift.models import Pallet


class BasemapsPallet(Pallet):
    def __init__(self):
        super().__init__()

        self.external = str(Path(self.staging_rack) / "external.gdb")

        self.copy_data = [self.external]

        self.geographic_transformation = None

    def build(self, configuration=None):
        self.add_crates(
            [
                (
                    "Public/Freeway_Exits/MapServer/0",
                    "https://roads.udot.utah.gov/server/rest/services/",
                    self.external,
                    "FreewayExitLocations",
                ),
                (
                    "Hosted/UTA_TRAX_Light_Rail_Routes/FeatureServer/0",
                    "https://maps.rideuta.com/server/rest/services/",
                    self.external,
                    "UTA_TRAX_Light_Rail_Routes",
                ),
                (
                    "Hosted/TRAX_Light_Rail_Stations/FeatureServer/0",
                    "https://maps.rideuta.com/server/rest/services/",
                    self.external,
                    "TRAX_Stations",
                ),
                (
                    "Hosted/FrontRunnerStations/FeatureServer/0",
                    "https://maps.rideuta.com/server/rest/services/",
                    self.external,
                    "FrontRunnerStations",
                ),
                (
                    "Hosted/UTA_FrontRunner_Commuter_Rail_Centerline/FeatureServer/0",
                    "https://maps.rideuta.com/server/rest/services/",
                    self.external,
                    "FrontRunnerCenterline",
                ),
            ]
        )
