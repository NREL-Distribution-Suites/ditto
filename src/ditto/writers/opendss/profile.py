from uuid import UUID

from ditto.writers.opendss.opendss_mapper import OpenDSSMapper
from ditto.enumerations import OpenDSSFileTypes

from infrasys.time_series_manager import TimeSeriesMetadata
from infrasys import Component, SingleTimeSeries, NonSequentialTimeSeries
from gdm.distribution import DistributionSystem


class ProfileMapper(OpenDSSMapper):
    opendss_file = OpenDSSFileTypes.LOADSHAPE_FILE.value
    altdss_name = None  ## Defined in the init function
    altdss_composition_name = "LoadShape"

    def __init__(self, component: Component, profile_datasets: dict, system: DistributionSystem):
        super().__init__(component, system)

        self.component: Component = component
        self.profile_datasets = profile_datasets
        self.model: TimeSeriesMetadata = profile_datasets[0]["profile"]
        self.metadata: list[TimeSeriesMetadata] = profile_datasets[0]["metadata"]

        if issubclass(self.model.__class__, SingleTimeSeries):
            self.altdss_name = "LoadShape_PMultQMultInterval"
        elif issubclass(self.model.__class__, NonSequentialTimeSeries):
            self.altdss_name = "LoadShape_PMultQMultHour"
        else:
            raise ValueError(f"Unsupported model type {self.model.__class__.__name__}")

        if self.metadata[0].user_attributes and "profile_name" in self.metadata[0].user_attributes:
            profile_name = self.metadata[0].user_attributes["profile_name"]
        else:
            profile_name = str(self.model.uuid)
        self.profile_name = profile_name

    def _get_profile_metadata(self, profile_uuid: UUID) -> TimeSeriesMetadata:
        for metadata in self.profile_datasets:
            for m in metadata["metadata"]:
                if m.time_series_uuid == profile_uuid:
                    return m

    def map_timestamps(self):
        t0 = self.model.timestamps[0]
        self.opendss_dict["Hour"] = [
            (t - t0).total_seconds() / 3600 for t in self.model.timestamps
        ]

    def map_variable_name(self):
        self.opendss_dict["Name"] = str(self.profile_name)

    def map_normalization(self):
        if self.model.normalization:
            self.opendss_dict["Action"] = "Normalize"
        else:
            self.opendss_dict["UseActual"] = True

    def map_data(self):
        if self.metadata[0].user_attributes and "profile_type" in self.metadata[0].user_attributes:
            for profile in self.profile_datasets:
                metadata = self._get_profile_metadata(profile["profile"].uuid)
                # units = profile["profile"].data.units
                data = profile["profile"].data.magnitude.tolist()
                self.opendss_dict[metadata.user_attributes["profile_type"]] = data
                # var = metadata.variable_name
                # variable_value = getattr(self.component, var).to(units).magnitude
                # if metadata.user_attributes['profile_type'] == "PMult":
                #     self.opendss_dict["PBase"] = variable_value
                #     self.opendss_dict["PMax"] = max(data)
                # else:
                #     self.opendss_dict["QBase"] = variable_value
                #     self.opendss_dict["QMax"] = max(data)

        else:
            if not len(self.profiles) == 1:
                msg = "If profile_type not specified for single time series, length of profiles must be 1"
                raise ValueError(msg)
            self.opendss_dict["PMult"] = self.model.data.magnitude.tolist()

    def map_resolution(self):
        self.opendss_dict["Interval"] = self.model.resolution.total_seconds() / 3600

    def map_initial_time(self):
        ...
