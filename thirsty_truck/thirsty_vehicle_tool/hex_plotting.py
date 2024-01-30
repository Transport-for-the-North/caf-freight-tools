"""
Creates hexbin plot with road network overlayed
"""
# standard imports
from __future__ import annotations
import pathlib
from typing import Optional

# third party imports

import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import numpy as np
from bokeh import io, models, plotting, palettes, layouts

from shapely import geometry

# local imports
from thirsty_vehicle_tool import input_output_constants, tv_logging


LOG = tv_logging.get_logger(__name__)


def hexbin_plot(
    points: gpd.GeoDataFrame,
    plotting_inputs: input_output_constants.ParsedPlottingInputs,
    title: str,
    operational: input_output_constants.Operational,
    max_colour_bar_scale: Optional[float] = None,
) -> input_output_constants.HexTilling:
    """Create hexbin plot and saves as a PNG

    create hexbin plot using matplotlib.pyplot hexbin,
    overlays a road network onto plot
    shows plot if user selected show_plots=True
    saves plot as .png

    Parameters
    ----------
    points : gpd.GeoDataFrame
        points to create hexbin plot
    plotting_inputs : input_output_constants.ParsedPlottingInputs
        plotting inputs parsed from the config file
    title : str
        title of the plot
    operational : input_output_constants.Operational
        operational inputs from the config file
    max_colour_bar_scale : Optional[float], optional
        maximum colour bar value, if left blank it is automatically scaled, by default None

    Returns
    -------
    input_output_constants.HexTilling
        hextilling calulated for plot
    """

    LOG.info(f"Producing {title}")
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_title(title)
    ax.set_xlabel("Easting")
    ax.set_ylabel("Northing")
    ax.set_aspect("equal")
    ax.set_facecolor("black")

    x_min = points["geometry"].x.min() - 2 * operational.hex_bin_width
    y_min = points["geometry"].y.min() - 2 * operational.hex_bin_width

    x_max = points["geometry"].x.max() + 2 * operational.hex_bin_width
    y_max = points["geometry"].y.max() + 2 * operational.hex_bin_width

    grid_size = int(((x_max - x_min) / (operational.hex_bin_width)))
    # setup hexbins
    if max_colour_bar_scale is None:
        hex_bin = ax.hexbin(
            points["geometry"].x,
            points["geometry"].y,
            C=points["trips"],
            cmap=input_output_constants.COLOUR_MAP,
            gridsize=grid_size,
            extent=(x_min, x_max, y_min, y_max),
            reduce_C_function=np.sum,
            vmin=0,
        )
    else:
        hex_bin = ax.hexbin(
            points["geometry"].x,
            points["geometry"].y,
            C=points["trips"],
            cmap=input_output_constants.COLOUR_MAP,
            gridsize=grid_size,
            extent=(x_min, x_max, y_min, y_max),
            reduce_C_function=np.sum,
            vmin=0,
            vmax=max_colour_bar_scale,
        )
    # create output
    hex_binning_params = input_output_constants.HexTilling.from_polycollection(
        hexbin=hex_bin
    )
    # colour bar
    cbar = fig.colorbar(hex_bin, ax=ax)
    cbar.set_label(input_output_constants.SCALE_LABEL)
    # remove scale
    cbar.set_ticks([])

    # plot road network
    # set colour maps
    road_network = plotting_inputs.roads
    road_network[road_network["class"] == input_output_constants.A_ROAD_LABEL].plot(
        ax=ax,
        color=input_output_constants.ROAD_COLOUR,
        linewidth=input_output_constants.A_ROAD_LINEWIDTH,
    )
    road_network[road_network["class"] == input_output_constants.MOTORWAY_LABEL].plot(
        ax=ax,
        color=input_output_constants.ROAD_COLOUR,
        linewidth=input_output_constants.MOTORWAY_LINEWIDTH,
    )

    ax.set_xbound(x_min, x_max)
    ax.set_ybound(y_min, y_max)

    # save and show plot
    file_name = title.replace(" ", "_") + ".png"
    fig.savefig(operational.output_folder / file_name)
    if operational.show_plots:
        plt.show(block=True)
    return hex_binning_params


def create_hex_bin_html(
    hex_bin: input_output_constants.HexTilling
    | dict[str, input_output_constants.HexTilling],
    plotting_inputs: input_output_constants.ParsedPlottingInputs,
    title: str,
    operational: input_output_constants.Operational,
) -> None:
    """create a bokeh html file thirsty vehicle map

    has hex system, road network and motorway junction and service station
     with hover functionality

    Parameters
    ----------
    hex_bin : input_output_constants.HexTilling | dict[str, input_output_constants.HexTilling]
        hextilling(s) for plot, if dict is used keys will be used for legend labels 
    plotting_inputs : input_output_constants.ParsedPlottingInputs
        plotting inputs - parsed from config
    title : str
        title of plot
    operational : input_output_constants.Operational
        operational inputs from config
    """
    # get data sources
    #   road network
    road_network = plotting_inputs.roads
    a_roads = road_network[road_network["class"] == input_output_constants.A_ROAD_LABEL]
    motorways = road_network[
        road_network["class"] == input_output_constants.MOTORWAY_LABEL
    ]

    a_road_source = get_lines_glyph_source(
        a_roads,
        input_output_constants.A_ROAD_LINEWIDTH,
        input_output_constants.ROAD_COLOUR,
    )
    a_road_source.data["name"] = a_roads["roadnumber"]

    motorway_source = get_lines_glyph_source(
        motorways,
        input_output_constants.MOTORWAY_LINEWIDTH,
        input_output_constants.ROAD_COLOUR,
    )
    motorway_source.data["name"] = motorways["roadnumber"]

    #   outlines source
    outlines_source = get_lines_glyph_source(
        plotting_inputs.outlines,
        input_output_constants.OUTLINE_WIDTH,
        input_output_constants.OUTLINE_COLOUR,
    )

    #   hex data
    if isinstance(hex_bin, input_output_constants.HexTilling):
        hex_source = {
            "Hexs": plotting.ColumnDataSource(
                {
                    "x": hex_bin.vertices_x,
                    "y": hex_bin.vertices_y,
                    "c": hex_bin.rgb,
                    "count": hex_bin.relative_count.round(),
                }
            )
        }
    else:
        hex_source = {}
        for key, value in hex_bin.items():
            hex_source[f"{key.capitalize()} Hexs"] = plotting.ColumnDataSource(
                {
                    "x": value.vertices_x,
                    "y": value.vertices_y,
                    "c": value.rgb,
                    "count": value.relative_count.round(),
                }
            )
    #   junction source

    junction_source = get_points_glyph_source(
        plotting_inputs.junctions,
        input_output_constants.JUNCTION_SHAPE,
        input_output_constants.JUNCTION_SIZE,
        input_output_constants.JUNCTION_COLOUR,
    )
    junction_source.data["number"] = plotting_inputs.junctions["number"]


    # plotting points source
    points_source = {}
    for points in plotting_inputs.plotting_points:
        temp_points_source = get_points_glyph_source(
        points["points"],
        points["shape"],
        points["size"],
        points["colour"],
    )

        temp_points_source.data["name"] = points["points"][points["hover_column_name"]]
        points_source[points["label"]] = temp_points_source
    #   labels source
    labels_source = get_points_glyph_source(
        plotting_inputs.map_labels,
        input_output_constants.LABEL_SHAPE,
        input_output_constants.LABEL_SHAPE_SIZE,
        input_output_constants.LABEL_SHAPE_COLOUR,
    )
    labels_source.data["name"] = plotting_inputs.map_labels["name"]
    # define glyphs

    hex_glyph = models.Patches(xs="x", ys="y", fill_color="c", line_color="c")
    line_glyph = models.MultiLine(xs="x", ys="y", line_color="lc", line_width="lw")
    scatter_glyph = models.Scatter(
        x="x", y="y", marker="m", size="s", fill_color="c", line_color="c"
    )
    # define plots geometry

    plot_height = 800
    cb_width = 10
    graph_width = 700

    # Setting up main plot

    plot = plotting.figure(
        title=title,
        width=graph_width,
        height=plot_height,
        match_aspect=True,
        tools=["pan", "box_zoom", "wheel_zoom", "undo", "reset", "save"],
    )

    plot.background_fill_color = "black"
    plot.xgrid.grid_line_color = None
    plot.ygrid.grid_line_color = None
    plot.title.align = "center"
    plot.title.text_font_size = "12pt"

    legend_items = []

    # plot hexes
    for key, value in hex_source.items():
        hex_renderer = plot.add_glyph(value, hex_glyph)
        hex_hover = models.HoverTool(
            renderers=[hex_renderer],
            tooltips=[(input_output_constants.SCALE_LABEL, "@count")],
        )
        plot.add_tools(hex_hover)
        legend_items.append(models.LegendItem(label=key, renderers=[hex_renderer]))

    # plot outlines

    outlines_renederer = plot.add_glyph(
        outlines_source,
        line_glyph,
    )
    legend_items.append(
        models.LegendItem(label="outlines", renderers=[outlines_renederer])
    )

    # plot roads

    a_road_renderer = plot.add_glyph(a_road_source, line_glyph)
    motorway_renderer = plot.add_glyph(motorway_source, line_glyph)
    road_hover = models.HoverTool(
        renderers=[a_road_renderer, motorway_renderer], tooltips=[("Road", "@name")]
    )
    plot.add_tools(road_hover)
    legend_items.append(models.LegendItem(label="A Roads", renderers=[a_road_renderer]))
    legend_items.append(
        models.LegendItem(label="Motorways", renderers=[motorway_renderer])
    )
    # plot junctions

    junctions_renderer = plot.add_glyph(junction_source, scatter_glyph)
    junction_hover = models.HoverTool(
        renderers=[junctions_renderer], tooltips=[("Junction", "@number")]
    )
    plot.add_tools(junction_hover)
    legend_items.append(
        models.LegendItem(label="Junctions", renderers=[junctions_renderer])
    )

    #plot points
    if len(points_source) != 0:
        for key, value in points_source.items():
            points_renderer = plot.add_glyph(value, scatter_glyph)
            points_hover = models.HoverTool(
                renderers=[points_renderer], tooltips=[(key, "@name")]
            )
            plot.add_tools(points_hover)

            legend_items.append(
                models.LegendItem(label=key, renderers=[points_renderer])
            )


    # plot labels

    plot.add_glyph(labels_source, scatter_glyph)

    labels_renderer = models.LabelSet(
        x="x",
        y="y",
        text="name",
        x_offset=0,
        y_offset=5,
        source=labels_source,
        text_font_size=input_output_constants.LABEL_TEXT_SIZE,
        text_color=input_output_constants.LABEL_TEXT_COLOUR,
    )
    plot.add_layout(labels_renderer)

    # legend

    plot.add_layout(models.Legend(items=legend_items))

    plot.legend.click_policy = "hide"

    # create colour bar
    color_mapper = models.LinearColorMapper(
        palette=palettes.inferno(256), low=0, high=100
    )
    colour_bar = models.ColorBar(
        color_mapper=color_mapper, location=(5, 6), bar_line_width=0.1
    )

    color_bar_plot = plotting.figure(
        title=input_output_constants.SCALE_LABEL,
        title_location="right",
        height=plot_height,
        width=cb_width,
        toolbar_location=None,
        min_border=0,
        outline_line_color=None,
    )

    color_bar_plot.add_layout(colour_bar, "right")
    color_bar_plot.title.align = "center"
    color_bar_plot.title.text_font_size = "8pt"

    layout = layouts.row(plot, color_bar_plot)
    file_name = title.replace(" ", "_") + ".html"
    io.output_file(operational.output_folder / file_name)
    io.show(layout)


def create_hex_shapefile(
    hex_bin: input_output_constants.HexTilling,
    file_name: str,
    output_folder: pathlib.Path,
) -> None:
    """creates hex shapefile from hex_bin

    Parameters
    ----------
    hex_bin : input_output_constants.HexTilling
        contains parameter for hex shapefile
    file_name : str
        file name of outputted shapefile
    output_folder : pathlib.Path
        folder to output shapefile to
    """
    hexs = pd.DataFrame({"x": hex_bin.vertices_x, "y": hex_bin.vertices_y})

    hexs["geometry"] = hexs.apply(
        lambda row: geometry.Polygon(zip(row["x"], row["y"])), axis=1
    )

    hexs = gpd.GeoDataFrame(hexs, geometry="geometry", crs=input_output_constants.CRS)

    hexs["rel_scale"] = hex_bin.relative_count
    output_folder.mkdir(exist_ok=True)
    input_output_constants.to_shape_file(output_folder / file_name, hexs.loc[:,["geometry", "rel_scale"]])


def get_lines_glyph_source(
    lines: gpd.GeoDataFrame, line_width: int, line_colour: str
) -> models.ColumnarDataSource:
    """create road column data source (add_glyph input)

    Parameters
    ----------
    lines : gpd.GeoDataFrame
        GDF containing geometries under "geometry" column
    line_width : int
        width of line
    line_colour : str
        colour of line

    Returns
    -------
    models.ColumnarDataSource
        road column data source
    """

    x = lines["geometry"].apply(lambda x: x.xy[0])
    y = lines["geometry"].apply(lambda x: x.xy[1])

    lines["line_width"] = line_width
    lines["line_colour"] = line_colour

    road_source = plotting.ColumnDataSource(
        {
            "x": x,
            "y": y,
            "lc": lines["line_colour"],
            "lw": lines["line_width"],
        }
    )

    return road_source


def get_points_glyph_source(
    points: gpd.GeoDataFrame, shape: str, size: int, point_colour: str
) -> plotting.ColumnDataSource:
    """generate a column data source for the scatter glyph

    Parameters
    ----------
    points : gpd.GeoDataFrame
        points to create data source
    shape : str
        shape of points to plot
    size : int
        size of points to plot
    point_colour : str
        colour of shapes to plot

    Returns
    -------
    plotting.ColumnDataSource
        points data source
    """
    points["colour"] = point_colour
    points["size"] = size
    points["shape"] = shape

    points_source = plotting.ColumnDataSource(
        {
            "x": points["geometry"].x,
            "y": points["geometry"].y,
            "c": points["colour"],
            "s": points["size"],
            "m": points["shape"],
        }
    )
    return points_source
