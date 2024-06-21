def cuencaindex(dem,cuenca,redDrenaje,sizekm2):
    
    """agregar la funcion la direccion de input de entrada para dem"""
    """luego agregar el output de salida para cuenca y redDrenaje"""
    """finalmente agregar un valor numerico para sizekm2"""

    import processing
    import geopandas as gpd
    import rasterio as rs

    #tamaño de cuenca 
    demMeta=rs.open(dem)
    resolucionArea= demMeta.res[0]*demMeta.res[1]
    area=(sizekm2*1000000)/resolucionArea

    ## 1 PREPROCESAMIENTO
    # 1.1 correccion del DEM

    correccionDem= processing.run("sagang:fillsinkswangliu", 
    {'ELEV':dem,
    'FILLED':'TEMPORARY_OUTPUT',
    'FDIR':'TEMPORARY_OUTPUT',
    'WSHED':'TEMPORARY_OUTPUT',
    'MINSLOPE':0.1,
    '--overwrite':True})

    print("correccion dem terminada")

    # 1.2 delimitacion cuenca

    cuencasRaster=processing.run("grass7:r.watershed", 
    {'elevation':correccionDem['FILLED'],
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
    'stream':'TEMPORARY_OUTPUT',
    'half_basin':'TEMPORARY_OUTPUT',
    'length_slope':'TEMPORARY_OUTPUT',
    'slope_steepness':'TEMPORARY_OUTPUT',
    'tci':'TEMPORARY_OUTPUT',
    'spi':'TEMPORARY_OUTPUT',
    'GRASS_REGION_PARAMETER':None,
    'GRASS_REGION_CELLSIZE_PARAMETER':0,
    'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':'','--overwrite':True})

    print("delimitacion_terminada")

    ##2 Poligonizacion de cuencas (2 procesos)

    #2.1 Poligonizar cuenca

    cuencaVectorial=processing.run("gdal:polygonize", 
    {'INPUT':cuencasRaster['basin'],
    'BAND':1,'FIELD':'DN','EIGHT_CONNECTEDNESS':False,'EXTRA':'',
    'OUTPUT':'TEMPORARY_OUTPUT',
    '--overwrite':True})

    print("poligonizacion_terminada")


    #2.2 Corregir geometria

    cuencaVectorialCorregido=processing.run("native:fixgeometries",
    {'INPUT':cuencaVectorial['OUTPUT'],
    'METHOD':1,
    'OUTPUT':'TEMPORARY_OUTPUT',
    '--overwrite':True})

    print("geometria_terminada")

    ##3 CALCULO DE RED DE DRENAJE (3 procesos)

    #3.1 vectorizacion de red de drenaje

    streamVect= processing.run("grass7:r.to.vect", 
    {'input':cuencasRaster['stream'],
    'type':0,'column':'value','-s':True,'-v':False,'-z':False,'-b':False,'-t':False,
    'output':'TEMPORARY_OUTPUT',
    'GRASS_REGION_PARAMETER':None,
    'GRASS_REGION_CELLSIZE_PARAMETER':0,
    'GRASS_OUTPUT_TYPE_PARAMETER':0,
    'GRASS_VECTOR_DSCO':'',
    'GRASS_VECTOR_LCO':'',
    'GRASS_VECTOR_EXPORT_NOCAT':False,
    '--overwrite':True})

    print("drenaje vectorial listo")

    #3.2 correccion geometrica de la red de drenaje

    streanVectCorrec= processing.run("native:fixgeometries", 
    {'INPUT':streamVect['output'],
    'METHOD':1,
    'OUTPUT':'TEMPORARY_OUTPUT',
    '--overwrite':True})

    print("correccion geometrica streams terminada")


    #3.3 disolucion de la red de drenaje

    streamDisolv= processing.run("native:dissolve", 
    {'INPUT':streanVectCorrec['OUTPUT'],
    'FIELD':[],
    'SEPARATE_DISJOINT':False,
    'OUTPUT':'TEMPORARY_OUTPUT',
    '--overwrite':True})

    print("disolucion drenaje terminado")

    #3.4 interseccion cuencas de drenaje

    intersecCuencas=  processing.run("native:intersection",
    {'INPUT':streamDisolv['OUTPUT'],
    'OVERLAY':cuencaVectorialCorregido['OUTPUT'],
    'INPUT_FIELDS':[],
    'OVERLAY_FIELDS':[],
    'OVERLAY_FIELDS_PREFIX':'',
    'OUTPUT':'TEMPORARY_OUTPUT',
    'GRID_SIZE':None})

    print("cuencas intersectadas")

    #3.5 Calculo de longuitud de red de drenaje (km)

    processing.run("native:fieldcalculator", 
    {'INPUT':intersecCuencas['OUTPUT'],
    'FIELD_NAME':'longuitud red drenaje (km)',
    'FIELD_TYPE':0,
    'FIELD_LENGTH':10,
    'FIELD_PRECISION':3,
    'FORMULA':'$length / 1000',
    'OUTPUT':redDrenaje,
    '--overwrite':True})

    print("longuitud de drenaje calculada")


    ##4 CALCULO DE PARAMETROS MORFOMETRICOS
    #4.1 Calculo de pendientes

    pendiente=processing.run("native:slope", 
    {'INPUT':correccionDem['FILLED'],
    'Z_FACTOR':1,
    'OUTPUT':'TEMPORARY_OUTPUT',
    '--overwrite':True})


    print("pendiente_terminada")

    #4.2 Estadistica zona altitude

    estadisticaZonal1=processing.run("native:zonalstatisticsfb", 
    {'INPUT':cuencaVectorialCorregido['OUTPUT'],
    'INPUT_RASTER':correccionDem['FILLED'],
    'RASTER_BAND':1,
    'COLUMN_PREFIX':'Altitud_',
    'STATISTICS':[2,5,6],
    'OUTPUT':'TEMPORARY_OUTPUT',
    '--overwrite':True})

    print("estadistica zonal 1 terminada")


    #4.3 Estadstica zona pendiente

    estadisticaZonal2= processing.run("native:zonalstatisticsfb", 
    {'INPUT':estadisticaZonal1['OUTPUT'],
    'INPUT_RASTER':pendiente['OUTPUT'],
    'RASTER_BAND':1,
    'COLUMN_PREFIX':'Pendiente_',
    'STATISTICS':[2],
    'OUTPUT':'TEMPORARY_OUTPUT',
    '--overwrite':True})

    print("estadistica zonal 2 terminada")

    #4.4 Calculo de area 

    areaCuencas= processing.run("native:fieldcalculator", 
    {'INPUT':estadisticaZonal2['OUTPUT'],
    'FIELD_NAME':'areaCuencakm2',
    'FIELD_TYPE':0,
    'FIELD_LENGTH':0,
    'FIELD_PRECISION':0,
    'FORMULA':' $area  / 1000000',
    'OUTPUT':'TEMPORARY_OUTPUT',
    '--overwrite':True})

    print("area calculada")

    #4.5 Calculo de perimetro

    perimetroCuenca= processing.run("native:fieldcalculator", 
    {'INPUT':areaCuencas['OUTPUT'],
    'FIELD_NAME':'perimetro',
    'FIELD_TYPE':0,
    'FIELD_LENGTH':0,
    'FIELD_PRECISION':0,
    'FORMULA':' $perimeter / 1000',
    'OUTPUT':'TEMPORARY_OUTPUT',
    '--overwrite':True})

    print("perimetro calculado")


    #4.6 relieve de la cuenca (R)  

    relieveCuencaR= processing.run("native:fieldcalculator",
    {'INPUT':perimetroCuenca['OUTPUT'],
    'FIELD_NAME':'relieveCuenca(R)',
    'FIELD_TYPE':0,
    'FIELD_LENGTH':0,
    'FIELD_PRECISION':0,
    'FORMULA':' "Altitud_max" - "Altitud_min" ',
    'OUTPUT':'TEMPORARY_OUTPUT',
    '--overwrite':True})

    print("Calculo de relieve listo")

    #4.7 meltons ruggedness number (M)

    meltonsRuggnes= processing.run("native:fieldcalculator", 
    {'INPUT':relieveCuencaR['OUTPUT'],
    'FIELD_NAME':'ruggedness number (M) ',
    'FIELD_TYPE':0,'FIELD_LENGTH':5,
    'FIELD_PRECISION':2,
    'FORMULA':' "relieveCuenca(R)" * (("areaCuencakm2" ) ^ (- 0.5) )',
    'OUTPUT':'TEMPORARY_OUTPUT',
    '--overwrite':True})

    print("M terminado")

    #4.8 Circularity of the basin (Circ)

    circularity= processing.run("native:fieldcalculator", 
    {'INPUT':meltonsRuggnes['OUTPUT'],
    'FIELD_NAME':'Circularidad ',
    'FIELD_TYPE':0,
    'FIELD_LENGTH':5,
    'FIELD_PRECISION':2,
    'FORMULA':'4 * pi() * ( "areaCuencakm2" / ("perimetro" ) ^ 2 )',
    'OUTPUT':'TEMPORARY_OUTPUT',
    '--overwrite':True})

    print("circularidad terminada")

    #4.9 Compacness factor 

    processing.run("native:fieldcalculator", 
    {'INPUT':circularity['OUTPUT'],
    'FIELD_NAME':'factor de compacidad ',
    'FIELD_TYPE':0,
    'FIELD_LENGTH':5,
    'FIELD_PRECISION':2,
    'FORMULA':' "perimetro"  / (2 * (( pi()* "areaCuencakm2" ) ^ 1/2)) ',
    'OUTPUT':cuenca,
    '--overwrite':True})

    print("calculo de parametros morfometricos terminado")
