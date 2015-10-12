#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

import sys
import importlib
import datetime
from optparse import OptionParser

import requests

from nupic.data.inference_shifter import InferenceShifter
from nupic.frameworks.opf.modelfactory import ModelFactory

import nupic_anomaly_output


DEFAULT_RIVER_VIEW_URL = "http://data.numenta.org"
DEFAULT_RIVER = "chicago-beach-weather"
DEFAULT_STREAM = "Oak Street Weather Station"
DEFAULT_FIELD = "solar_radiation"
DEFAULT_PLOT = False
DEFAULT_DATA_LIMIT = 3000

DATETIME_FIELDNAME = 'datetime'
# 2015/08/19 12:00:00
DATE_FORMAT = "%Y/%m/%d %H:%M:%S"

# Options parsing.
parser = OptionParser(
  usage="%prog [options]\n\n"
        """
Creates a NuPIC anomaly model using one field of one stream of one River in
River View.
        """
)
parser.add_option(
  "-p",
  "--plot",
  action="store_true",
  default=DEFAULT_PLOT,
  dest="plot",
  help="Plot results in matplotlib instead of writing to file "
       "(requires matplotlib).")
parser.add_option(
  "-u",
  "--url",
  default=DEFAULT_RIVER_VIEW_URL,
  dest="url",
  help="Allows you to provide URL to custom River View instance.")
parser.add_option(
  "-r",
  "--river",
  default=DEFAULT_RIVER,
  dest="river",
  help="Which River to use.")
parser.add_option(
  "-s",
  "--stream",
  default=DEFAULT_STREAM,
  dest="stream",
  help="Which Stream in the River to pull data from.")
parser.add_option(
  "-f",
  "--field",
  default=DEFAULT_FIELD,
  dest="field",
  help="Which field of data within stream to build anomaly model on.")
parser.add_option(
  "-a",
  "--aggregate",
  default=None,
  dest="aggregate",
  help="How should the data be aggregated (default None). If provided, the -f "
       "option is ignored. This only works with geospatial rivers.")



def getModelParams(min, max):
  params = importlib.import_module("model_params.anomaly_params").MODEL_PARAMS
  params['modelParams']['sensorParams']['encoders']['value']['minval'] = min
  params['modelParams']['sensorParams']['encoders']['_classifierInput']['minval'] = min
  params['modelParams']['sensorParams']['encoders']['value']['maxval'] = max
  params['modelParams']['sensorParams']['encoders']['_classifierInput']['maxval'] = max
  # import pprint; pprint.pprint(params)
  return params



def createModel(modelParams):
  model = ModelFactory.create(modelParams)
  model.enableInference({"predictedField": "value"})
  return model



def fetchData(url, river, stream, aggregate, params=None):
  if params is None and aggregate is None:
    params = {'limit': DEFAULT_DATA_LIMIT}
  targetUrl = "%s/%s/%s/data.json" % (url, river, stream)
  if aggregate:
    targetUrl += "?aggregate=%s" % aggregate
  print "Fetching data from %s..." % targetUrl
  response = requests.get(targetUrl, params=params)
  if response.status_code == 404:
    raise Exception('The River or stream provided does not exist:\n%s'
                    % targetUrl)
  data = response.json()
  if not data['type'] == 'scalar' and aggregate is None:
    raise Exception('Cannot process Rivers unless they are scalar.\n%s does '
                    'not return scalar data.' % targetUrl)
  return data



def getMinMax(data, field):
  min = None
  max = None
  headers = data['headers']
  payload = data['data']
  try:
    fieldIndex = headers.index(field)
  except ValueError:
    raise Exception('The field name "%s" does not exist in the given stream.'
                    % field)
  for point in payload:
    value = point[fieldIndex]
    if min is None:
      min = value
      max = value
    if value is not None:
      if value < min:
        min = value
      if value > max:
        max = value
  return (min, max)


def runModel(model, data, field, plot):
  fieldIndex = data['headers'].index(field)
  datetimeIndex = data['headers'].index(DATETIME_FIELDNAME)

  shifter = InferenceShifter()
  if plot:
    output = nupic_anomaly_output.NuPICPlotOutput(field)
  else:
    output = nupic_anomaly_output.NuPICFileOutput(field)

  for dataPoint in data['data']:
    dateString = dataPoint[datetimeIndex]
    timestamp = datetime.datetime.strptime(dateString, DATE_FORMAT)
    value = dataPoint[fieldIndex]
    if value is not None:
      result = model.run({
        "timestamp": timestamp,
        "value": value
      })
      if plot:
        result = shifter.shift(result)
      prediction = result.inferences["multiStepBestPredictions"][1]
      anomalyScore = result.inferences["anomalyScore"]
      output.write(timestamp, value, prediction, anomalyScore)

  output.close()



if __name__ == "__main__":
  (options, args) = parser.parse_args(sys.argv[1:])

  plot = options.plot
  river = options.river
  stream = options.stream
  field = options.field
  url = options.url
  aggregate = options.aggregate
  
  if aggregate:
    field = 'count'

  data = fetchData(url, river, stream, aggregate)
  (min, max) = getMinMax(data, field)

  modelParams = getModelParams(min, max)
  model = createModel(modelParams)
  runModel(model, data, field, plot)
