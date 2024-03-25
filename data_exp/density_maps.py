import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap



def create_density(grid_size):

    gdf = gpd.read_file("uni_ecoregions/tiles_100k.geojson")
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
        # print(index)
        tile_center = row['geometry'].centroid
        possible_matches_index = list(gdf_sindex.intersection(tile_center.bounds))
        
        for i in possible_matches_index:
            if gdf.loc[i, 'geometry'].contains(tile_center):
                x_idx = int((tile_center.x - min_x) / grid_size)
                y_idx = int((tile_center.y - min_y) / grid_size)
                grid_counts[x_idx][y_idx] += 1

    fig, ax = plt.subplots()
    grid_counts = np.transpose(grid_counts)

    im = ax.imshow(grid_counts, extent=(min_x, max_x, min_y, max_y), origin='lower', cmap='inferno')
    im.set_clim(0, 50) # this is hardcoded for grid_size = 1
    # im.set_clim(-2, 15) # this is hardcoded for grid_size = 0.1

    plt.colorbar(im, fraction=0.020, pad=0.04)


    # plt.show()
    plt.savefig(f"grid_{grid_size}_uni_eco.png", dpi=300)


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
    # create_density(1)
    # create_density(0.1)
    # create_density(0.01)
    create_density_custom(1)






