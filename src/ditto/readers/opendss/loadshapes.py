from datetime import datetime, timedelta

from infrasys.time_series_models import SingleTimeSeries
import opendssdirect as odd
from loguru import logger


def get_loadshapes() -> list[SingleTimeSeries]:
    """Function to return list of SingleTimeSeries objscts representing load shapes in the Opendss model.

    Returns:
        List[SingleTimeSeries]: List of SingleTimeSeries objects
    """

    logger.info("parsing timeseries components...")

    timeseries_objects = []
    flag = odd.LoadShape.First()
    while flag:
        data = odd.LoadShape.PMult()
        length = odd.LoadShape.Npts()
        initial_time = datetime(year=2020, month=1, day=1)
        resolution = timedelta(seconds=odd.LoadShape.SInterval())
        time_array = [initial_time + timedelta(seconds=i * resolution) for i in range(length)]
        variable_name = odd.LoadShape.Name()
        ts = SingleTimeSeries.from_time_array(data, variable_name, time_array)
        timeseries_objects.append(ts)
        flag = odd.LoadShape.Next()

    return timeseries_objects
