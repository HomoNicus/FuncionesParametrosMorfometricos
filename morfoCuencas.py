

def cuencastat(dem,cuencas,sizekm2):
    """help: puedes colocar lo que necesitas para ayudar"""
    """Para definir los parametros a evaluar en nuestro DEM, debemos definir:
        dem: Ruta de entrada del modelo de elevacion a evaluar
        cuencas: ruta de salida del DEM a evaluar
        sizekm2: tamano del pixel a evaluar, destacando de que es un parametro numerico. ej: 10)"""


    import processing
    import rasterio as rs

    # tamano de cuenca

    demMeta=rs.open(dem)
    resolucionArea= demMeta.res[0]*demMeta.res[1]
    area=(sizekm2*1000000)/resolucionArea
    
    
    #Delimitacion de cuenca

    cuencasRaster=processing.run("grass7:r.watershed", {'elevation':dem,
    'depression':None,
    'flow':None,
    'disturbed_land':None,
    'blocking':None,
    'threshold':area,
    'max_slope_length':None,
    'convergence':5,
    'memory':300,
    '-s':False,'-m':False,'-4':False,'-a':False,'-b':False,
    'accumulation':'TEMPORARY_OUTPUT',
    'drainage':'TEMPORARY_OUTPUT',
    'basin':'TEMPORARY_OUTPUT',
    'half_basin':'TEMPORARY_OUTPUT',
    'length_slope':'TEMPORARY_OUTPUT',
    'slope_steepness':'TEMPORARY_OUTPUT',
    'tci':'TEMPORARY_OUTPUT',
    'spi':'TEMPORARY_OUTPUT',
    'GRASS_REGION_PARAMETER':None,
    'GRASS_REGION_CELLSIZE_PARAMETER':0,
    'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':'','--overwrite':True})


    print("delimitacion_terminada")


    #Poligonizar cuenca

    cuencaVectorial=processing.run("gdal:polygonize", 
    {'INPUT':cuencasRaster['basin'],
    'BAND':1,'FIELD':'DN','EIGHT_CONNECTEDNESS':False,'EXTRA':'',
    'OUTPUT':'TEMPORARY_OUTPUT',
    '--overwrite':True})

    print("poligonizacion_terminada")


    #Corregir geometria

    cuencaVectorialCorregido=processing.run("native:fixgeometries",
    {'INPUT':cuencaVectorial['OUTPUT'],
    'METHOD':1,
    'OUTPUT':'TEMPORARY_OUTPUT',
    '--overwrite':True})

    print("geometria_terminada")

    #Calculo de pendientes

    pendiente=processing.run("native:slope", 
    {'INPUT':dem,
    'Z_FACTOR':1,
    'OUTPUT':'TEMPORARY_OUTPUT',
    '--overwrite':True})


    print("pendiente_terminada")


    #Estadistica zona altitude

    estadisticaZonal1=processing.run("native:zonalstatisticsfb", 
    {'INPUT':cuencaVectorialCorregido['OUTPUT'],
    'INPUT_RASTER':dem,
    'RASTER_BAND':1,
    'COLUMN_PREFIX':'Altitud_',
    'STATISTICS':[2,5,6],
    'OUTPUT':'TEMPORARY_OUTPUT',
    '--overwrite':True})

    print("estadistica zonal 1 terminada")



    #Estadstica zona pendiente

    processing.run("native:zonalstatisticsfb", 
    {'INPUT':estadisticaZonal1['OUTPUT'],
    'INPUT_RASTER':pendiente['OUTPUT'],
    'RASTER_BAND':1,
    'COLUMN_PREFIX':'Pendiente_',
    'STATISTICS':[2,5,6],
    'OUTPUT':cuencas,
    '--overwrite':True})

    print("estadistica zonal 2 terminada")
        

