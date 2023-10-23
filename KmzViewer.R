# Carga de bibliotecas
library(sf)
library(mapview)

# Ruta y descompresión del archivo KMZ
kmz_path <- "C:/Users/Contreras/Downloads/kmz/Area de Estudio Ambiental Romina.kmz"
unzip(kmz_path, exdir = tempdir())

# Identificación del archivo KML descomprimido
kml_file <- list.files(tempdir(), pattern = "*.kml", full.names = TRUE, recursive = TRUE)[1]

# Lectura del archivo KML
layers <- st_layers(kml_file)
kmz_data_layer1 <- st_read(kml_file, layer = layers$name)

# Conversión a geometría 2D
kmz_data_2d <- st_zm(kmz_data_layer1, drop=TRUE, what="ZM")

# Visualización de los datos
mapview(kmz_data_2d)
