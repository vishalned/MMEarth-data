import matplotlib.pyplot as plt
import json
import numpy as np
import h5py


# tile_path = "/home/qbk152/vishal/global-lr/data/data_1M_130_tile_info.json"
# tile_path = "/home/qbk152/vishal/global-lr/data/data_tmp_tile_info.json"
# data_path = '/home/qbk152/vishal/global-lr/data/tmp.h5'
# tile_info = json.load(open(tile_path))

def month_only(args):
    '''
    Plot the number of tiles per month
    '''

    tile_info = json.load(open(args.tile_info_path))
    month = np.arange(1, 13)
    month_counts = np.zeros(12)
    for tile in tile_info:
        month_counts[int(tile_info[tile]['S2_DATE'].split('-')[1]) - 1] += 1

    plt.bar(month, month_counts)
    plt.xlabel('Month')
    plt.ylabel('Number of tiles')
    plt.title('Number of tiles per month')

    plt.savefig(os.path.join(args.store_path, 'month_counts.png'))

    plt.clf()
    # stats about which months in a year are present in the dataset

def s2_type(args):
    '''
    Plot the number of tiles per month per year
    '''
    tile_info = json.load(open(args.tile_info_path))
    month = np.arange(1, 12*4 + 1)
    month_counts_l1c = np.zeros(12*4)
    month_counts_l2a = np.zeros(12*4)

    for tile in tile_info:
        m = int(tile_info[tile]['S2_DATE'].split('-')[1])
        y = int(tile_info[tile]['S2_DATE'].split('-')[0])
        if tile_info[tile]['S2_type'] == 'l1c':
            month_counts_l1c[(y - 2017) * 12 + m - 1] += 1
        else:
            month_counts_l2a[(y - 2017) * 12 + m - 1] += 1

    years = np.arange(2017, 2021)
    yearly_counts_l1c = [month_counts_l1c[i:i+12] for i in range(0, len(month_counts_l1c), 12)]
    yearly_counts_l2a = [month_counts_l2a[i:i+12] for i in range(0, len(month_counts_l2a), 12)]



    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'] * 4
    month_labels = [f"{years[i // 12]} {month_names[i]}" for i in range(12*4)]
    year_colors = ['b', 'g', 'r', 'c']


    # print(np.sum(yearly_counts_l1c))

    # Create a bar plot for each year
    for i, year_count in enumerate(yearly_counts_l1c):
        plt.bar(np.arange(12*i + 1, 12*i + 13), year_count, label=str(years[i]), color=year_colors[i], alpha=0.7)

    plt.xticks(np.arange(1, 12 * 4 + 1), month_labels, rotation=90, fontsize=6)
    plt.xlabel('Month')
    plt.ylabel('Count')
    plt.title('Monthly Counts by Year')
    plt.legend(title='Year')
    # increase the spacing between each bar plot
    plt.tight_layout()
    plt.savefig(os.path.join(args.store_path, 'yearly_counts_l1c.png'))
    plt.clf()

    for i, year_count in enumerate(yearly_counts_l2a):
        plt.bar(np.arange(12*i + 1, 12*i + 13), year_count, label=str(years[i]), color=year_colors[i], alpha=0.7)

    plt.xticks(np.arange(1, 12 * 4 + 1), month_labels, rotation=90, fontsize=6)
    plt.xlabel('Month')
    plt.ylabel('Count')
    plt.title('Monthly Counts by Year')
    plt.legend(title='Year')
    # increase the spacing between each bar plot
    plt.tight_layout()
    plt.savefig(os.path.join(args.store_path, 'yearly_counts_l2a.png'))




def month_year(args):
    '''
    Plot the number of tiles per month per year
    '''
    tile_info = json.load(open(args.tile_info_path))
    month = np.arange(1, 12*4 + 1)
    month_counts = np.zeros(12*4)

    for tile in tile_info:
        m = int(tile_info[tile]['S2_DATE'].split('-')[1])
        y = int(tile_info[tile]['S2_DATE'].split('-')[0])
        month_counts[(y - 2017) * 12 + m - 1] += 1
    years = np.arange(2017, 2021)
    yearly_counts = [month_counts[i:i+12] for i in range(0, len(month_counts), 12)]

    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'] * 4
    month_labels = [f"{years[i // 12]} {month_names[i]}" for i in range(12*4)]
    year_colors = ['b', 'g', 'r', 'c']

    # Create a bar plot for each year
    for i, year_count in enumerate(yearly_counts):
        plt.bar(np.arange(12*i + 1, 12*i + 13), year_count, label=str(years[i]), color=year_colors[i], alpha=0.7)

    plt.xticks(np.arange(1, 12 * 4 + 1), month_labels, rotation=90, fontsize=6)
    plt.xlabel('Month')
    plt.ylabel('Count')
    plt.title('Monthly Counts by Year')
    plt.legend(title='Year')
    # increase the spacing between each bar plot
    plt.tight_layout()
    plt.savefig(os.path.join(args.store_path, 'yearly_counts.png'))
    plt.clf()


def dynamic_world(args):
    '''
    Plot the number of pixels per class in the dynamic world dataset
    '''
    class_names = [
        "No data",
        "Water",
        "Trees",
        "Grass",
        "Flooded vegetation",
        "Crops",
        "Shrub and scrub",
        "Built",
        "Bare",
        "Snow and ice"
    ]

    hdf5_file = h5py.File(args.data_path, 'r')
    meta = hdf5_file['metadata']    
    dw_count = {i:0 for i in range(0, 10)}

    num_tiles = len(meta)
    for i in range(num_tiles):
        tile_id = meta[i][0].decode('utf-8')
        img = hdf5_file['dynamic_world'][i]

        # obtain the number of pixels in each class
        for j in range(10):
            dw_count[j] += np.sum(img == j)

        if i % 1000 == 0:
            print(f"Processed {i} tiles")


    plt.bar(dw_count.keys(), dw_count.values())
    plt.xticks(np.arange(0, 10), class_names, rotation=90, fontsize=8)
    plt.subplots_adjust(bottom=0.4)
    
    plt.xlabel('Class')
    plt.ylabel('Number of pixels')
    plt.title('Number of pixels per class')

    plt.savefig(os.path.join(args.store_path, 'dw_counts.png'))


def esa_worldcover(args):
    class_names = [
        'Tree cover',
        'Shrubland',
        'Grassland',
        'Cropland',
        'Built-up',
        'Bare / sparse vegetation',
        'Snow and ice',
        'Permanent water bodies',
        'Herbaceous wetland',
        'Mangroves',
        'Moss and lichen'
    ]
    class_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
    hdf5_file = h5py.File(args.data_path, 'r')
    meta = hdf5_file['metadata'] 
    esa_count = {i:0 for i in class_values}

    num_tiles = len(meta)
    for i in range(num_tiles):
        tile_id = meta[i][0].decode('utf-8')
        img = hdf5_file['esa_worldcover'][i]

        # obtain the number of pixels in each class
        for j in class_values:
            esa_count[j] += np.sum(img == j)



        if i % 1000 == 0:
            print(f"Processed {i} tiles")
            
    plt.bar(esa_count.keys(), esa_count.values(), width=7)
    plt.xticks(class_values, class_names, rotation=90, fontsize=8)
    plt.subplots_adjust(bottom=0.4)

    plt.xlabel('Class')
    plt.ylabel('Number of pixels')
    plt.title('Number of pixels per class')

    plt.savefig(os.path.join(args.store_path, 'esa_counts.png'))

        

def custom(args):
    '''
    Trying to plot the number of tiles per grid cell for the tiles that have the date as dec 2018
    '''
    minx, miny, maxx, maxy = -179.9863841350967, -86.78204367236995, 180.05963072575278, 83.48337010728358
    grid_size = 1
    tile_info = json.load(open(args.tile_info_path))

    x = np.arange(minx, maxx + grid_size, grid_size)
    y = np.arange(miny, maxy + grid_size, grid_size)

    grid_counts = np.zeros((len(x) - 1, len(y) - 1))
    count = 0

    for tile in tile_info:
        m = int(tile_info[tile]['S2_DATE'].split('-')[1])
        y = int(tile_info[tile]['S2_DATE'].split('-')[0])

        if m == 12 and y == 2018:
            lon, lat = tile_info[tile]['lon'], tile_info[tile]['lat']

        
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
    plt.savefig(os.path.join(args.store_path, f"grid_{grid_size}.png"), dpi=300)


def dw_custom(args):
    '''
    Plot the tiles per grid for a specific dw class
    '''
    minx, miny, maxx, maxy = -179.9863841350967, -86.78204367236995, 180.05963072575278, 83.48337010728358
    grid_size = 1
    tile_info = json.load(open(args.tile_info_path))


    x = np.arange(minx, maxx + grid_size, grid_size)
    y = np.arange(miny, maxy + grid_size, grid_size)

    grid_counts = np.zeros((len(x) - 1, len(y) - 1))
    count = 0

    hdf5_file = h5py.File(args.data_path, 'r')
    meta = hdf5_file['metadata']    


    num_tiles = len(meta)
    for i in range(num_tiles):
        tile = meta[i][0].decode('utf-8')
        img = hdf5_file['dynamic_world'][i]
        if np.sum(img == 0) > 1000:
            lon, lat = tile_info[tile]['lon'], tile_info[tile]['lat']

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
    
    # plt.show()
    plt.colorbar(im, fraction=0.020, pad=0.04)
    plt.savefig(os.path.join(args.store_path, f"grid_{grid_size}.png"), dpi=300)


def era_stats(args):
    '''
    Plot the distribution of temperature for each tile.
    '''

    hdf5_file = h5py.File(args.data_path, 'r')
    meta = hdf5_file['metadata']
    num_tiles = len(meta)
    data_month = []

    for i in range(num_tiles):
        tile = meta[i][0].decode('utf-8')
        data = hdf5_file['era5'][i][4:8]
        data_month.append(data[0])


    data_month = np.array(data_month) - 273.15

    # plot the distribution of temperature for each tile

    fig, ax = plt.subplots()
    ax.hist(data_month, bins=100)

    plt.xlabel('Temperature (C)')
    plt.ylabel('Number of tiles')
    plt.title('Distribution of Monthly Temperature for Each Tile')

    plt.savefig(os.path.join(args.store_path, 'era5_temperature.png'))


def aster_stats(args):
    '''
    Plot the distribution of elevation for each tile.
    '''
    hdf5_file = h5py.File(args.data_path, 'r')
    meta = hdf5_file['metadata']
    num_tiles = len(meta)

    bins = np.arange(-170, 6500, 10)

    hist_counts = np.zeros(len(bins))
    min_, max_ = 100000, -100000
    for i in range(num_tiles):
        img = hdf5_file['aster'][i]
        # Extract the elevation band
        data = img[0, :, :]

        data = data.flatten()
        # if np.min(data) < min_:
        #     min_ = np.min(data)

        # if np.max(data) > max_:
        #     max_ = np.max(data)
        ind = np.digitize(data, bins=bins)
        ind = ind - 1
        hist_counts[ind] += 1

        if i % 1000 == 0:
            print(f"Processed {i} tiles")


    hdf5_file.close()

    # print("Min and max elevation")
    # print(min_, max_)
    # Plot the histogram with bin labels
    fig, ax = plt.subplots()
    ax.bar(bins, hist_counts, width=100)
    plt.xlabel('Elevation (m)')
    plt.ylabel('Number of pixels')
    plt.title('Distribution of Elevation for All Tiles')

    plt.savefig(os.path.join(args.store_path, 'aster_elevation.png'))
    




    

if __name__ == '__main__':

    import argparse
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, required=True)
    parser.add_argument('--store_path', type=str, default='/home/qbk152/vishal/global-lr/data_exp')
    args = parser.parse_args()


    name = args.data_dir.split('/')[-1] if args.data_dir[-1] != '/' else args.data_dir.split('/')[-2]
    args.tile_info_path = os.path.join(args.data_dir, name + '_tile_info.json')
    args.data_path = os.path.join(args.data_dir, name + '.h5')
    args.store_path = os.path.join(args.store_path, name)
    if not os.path.exists(args.store_path):
        os.makedirs(args.store_path)

    print('storing plots in', args.store_path)


    
    month_only(args)
    month_year(args)
    s2_type(args)
    dynamic_world(args)
    # era_stats()
    # aster_stats()
    esa_worldcover(args)



