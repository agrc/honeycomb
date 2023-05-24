from time import sleep

while True:
    try:
        import arcpy

        print('license found')
        break
    except:
        print('no license available, waiting...')
        sleep(10)
