import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import json
# world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))


def create_density(grid_size):

    gdf = gpd.read_file("/projects/dereeco/data/global-lr/geojson_files/tiles_1M_v001.geojson")
    json_ = json.load(open("/projects/dereeco/data/global-lr/data_1M_v001/data_1M_v001_tile_info.json"))
    # gdf = gpd.read_file("/home/qbk152/vishal/global-lr/tile_polygons/uni_biomes_only/tiles_100k_130.geojson")
    grid_size = grid_size
    min_x, min_y, max_x, max_y = gdf.total_bounds
    # print(min_x, min_y, max_x, max_y)
    # exit()

    # Create grid cells
    x = np.arange(min_x, max_x + grid_size, grid_size)
    y = np.arange(min_y, max_y + grid_size, grid_size)
    grid_counts = np.zeros((len(x) - 1, len(y) - 1))


    gdf_sindex = gdf.sindex

    for index, row in gdf.iterrows():
        # if index % 10000 == 0:
        tile_center = row['geometry'].centroid
        possible_matches_index = list(gdf_sindex.intersection(tile_center.bounds))
        name = row['tile_id']
        
        
        # we only want to count the number of samples for l2a tiles
        try:
            if json_[name]['S2_type'] == "l2a":
                continue
        except:
            # the name is not in the json file
            continue
        
        for i in possible_matches_index:
            # ensure the possible matches are l2a tiles
            try:
                if json_[gdf.loc[i, 'tile_id']]['S2_type'] == "l2a":
                    continue
            except:
                continue
            if gdf.loc[i, 'geometry'].contains(tile_center):
                x_idx = int((tile_center.x - min_x) / grid_size)
                y_idx = int((tile_center.y - min_y) / grid_size)
                grid_counts[x_idx][y_idx] += 1

    # fig, ax = plt.subplots()
    # grid_counts = np.transpose(grid_counts)
    # world.boundary.plot(
    # ax=ax,
    # color="gray",
    # # edgecolor="black",
    # linewidth=0.4
    # )


    # cmap = plt.cm.get_cmap('inferno')

    # ax.set_xticks([])
    # ax.set_yticks([])
    
    # im = ax.imshow(grid_counts, extent=(min_x, max_x, min_y, max_y), origin='lower', cmap='inferno')


    # im.set_clim(1, 1000) 
    # cbar = plt.colorbar(im, fraction=0.020, pad=0.04)
    # cbar.ax.set_ylabel('Number of samples', rotation=90, labelpad=2)
    # y_tick_labels = [str(i) for i in range(0, 801, 200)]
    # y_tick_labels.append(">1k")
    # cbar.ax.set_yticklabels(y_tick_labels)
    # plt.rcParams.update({'font.size': 6})

    # # plt.show()
    # plt.savefig(f"/home/qbk152/vishal/global-lr/data_exp/t-grid_{grid_size}_uni_biomes.png", dpi=300, format='png')
    # plt.savefig(f"/home/qbk152/vishal/global-lr/data_exp/t-grid_{grid_size}_uni_biomes.pdf", dpi=300, format='pdf')
    from matplotlib.colors import ListedColormap
    fig, ax = plt.subplots()
    plt.rcParams.update({'font.size': 9})
    plt.rcParams.update({'figure.figsize': (8, 6)})
    grid_counts = np.transpose(grid_counts)
    # world.boundary.plot(
    #     ax=ax,
    #     color="white",
    #     linewidth=0.5
    # )

    # Create custom colormap
    colors = plt.cm.inferno(np.linspace(0, 1, 256))
    colors[0] = (1, 1, 1, 0)  # Set color for 0 to white (or (1,1,1,0) for transparent)
    custom_cmap = ListedColormap(colors)

    ax.set_xticks([])
    ax.set_yticks([])

    im = ax.imshow(grid_counts, extent=(min_x, max_x, min_y, max_y), origin='lower', cmap=custom_cmap)

    
    # Adjust color limits

    # im.set_clim(0, 1000)  # this is hardcoded for grid_size = 1
    im.set_clim(0, 600)

    cbar = plt.colorbar(im, fraction=0.020, pad=0.04)
    cbar.ax.set_ylabel('Number of samples', rotation=90, labelpad=2)
    y_tick_labels = ["1", "100", "200", "300", "400", "500", ">600"]
    y_tick_loc = [1, 100, 200, 300, 400, 500, 600]
    cbar.set_ticks(y_tick_loc)
    cbar.ax.set_yticklabels(y_tick_labels)

    plt.savefig(f"/home/qbk152/vishal/MMEarth-data/1M_v001_plots/data_1M_v001/grid_{grid_size}_uni_biomes_whitebg_L1C.png", dpi=300, format='png', bbox_inches='tight')
    plt.savefig(f"/home/qbk152/vishal/MMEarth-data/1M_v001_plots/data_1M_v001/grid_{grid_size}_uni_biomes_whitebg_L1C.pdf", dpi=300, format='pdf', bbox_inches='tight')
    # plt.show()



def create_density_custom(grid_size):
    file = open("data/missing_tiles_1M.csv")
    lines = file.readlines()

    minx, miny, maxx, maxy = -179.9863841350967, -86.78204367236995, 180.05963072575278, 83.48337010728358
    grid_size = 1

    x = np.arange(minx, maxx + grid_size, grid_size)
    y = np.arange(miny, maxy + grid_size, grid_size)

    grid_counts = np.zeros((len(x) - 1, len(y) - 1))
    count = 0

    for line in lines:
        tile_id, lat, lon = line.split(",")
        lat = float(lat)
        lon = float(lon)

        x_idx = int((lon - minx) / grid_size)
        y_idx = int((lat - miny) / grid_size)

        grid_counts[x_idx][y_idx] += 1
        count += 1


    print(count)
    
    fig, ax = plt.subplots()
    grid_counts = np.transpose(grid_counts)

    im = ax.imshow(grid_counts, extent=(minx, maxx, miny, maxy), origin='lower', cmap='inferno')
    im.set_clim(0, 50) # this is hardcoded for grid_size = 1
    # im.set_clim(-2, 15) # this is hardcoded for grid_size = 0.1

    plt.colorbar(im, fraction=0.020, pad=0.04)


    # plt.show()
    plt.savefig(f"data_exp/missing_tiles_1M_{grid_size}.png", dpi=300)


if __name__ == "__main__":
    create_density(1.1)
    # create_density(0.1)
    # create_density(0.01)
    # create_density_custom(1)






