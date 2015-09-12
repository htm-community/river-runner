# River Runner

This is a Python project that runs NuPIC **anomaly detection** models against data in a [River View](https://github.com/nupic-community/river-view) instance. It constructs a NuPIC model using model parameters proven to work well for scalar anomalies. Then, given a river name, stream id, and field name, will pull data from River View and push each scalar data point into the newly created model.

## Requires

- matplotlib (if you want to use the `--plot` option) [recommended]
- [requests](http://www.python-requests.org/)
- [NuPIC](https://github.com/numenta/nupic)

## Run it

    ./run.py

With no options, this script will fetch [Chicago Beach Weather at Oak Street Weather Station](http://data.numenta.org/chicago-beach-weather/Oak%20Street%20Weather%20Station/data.html?limit=500), use the `solar_radiation` field to pass into the NuPIC model, and write the output to a file.

## Plot it

This example is much more compelling if you plot the output. If you do not have matplotlib installed, you can always use a local spreadsheet program to plot the predictions and results. But if you have matplotlib, just run with the `--plot` option to plot.

## Options

You can specify options on the command line for other rivers / streams / fields:

```
Options:
  -h, --help            show this help message and exit
  -p, --plot            Plot results in matplotlib instead of writing to file
                        (requires matplotlib).
  -u URL, --url=URL     Allows you to provide URL to custom River View
                        instance.
  -r RIVER, --river=RIVER
                        Which River to use.
  -s STREAM, --stream=STREAM
                        Which Stream in the River to pull data from.
  -f FIELD, --field=FIELD
                        Which field of data within stream to build anomaly
                        model on.
```

## Example

The following will fetch data from the [ERCOT System Wide Demand](http://data.numenta.org/ercot-demand/system_wide_demand/data.html?limit=500) stream, analyzing and plotting the `Demand` field.

    ./run.py -r ercot-demand -s system_wide_demand -f Demand --plot

## A Note about predictions...

While the plot and the output file contains predictions from the NuPIC model, the model parameters used to create the model were not optimized for prediction. Therefore, the predictions will very likely be inaccurate. This example program is best suited for identifying anomalies within River data streams.
