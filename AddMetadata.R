library(sf)
library(rgee)

add_metadata_to_geojson <- function(geojson_path, name, metadata) {
  # Cargar geojson
    geojson <- st_read(geojson_path)
  
    # Autenticar con Google Earth Engine
    # Nota: Descomentar si la inicialización no ha sido hecha previamente en la sesión de R
    # ee_Initialize()

    for (meta in metadata) {
        if (name == "TM") {
            image_ids <- geojson$tm_id
        } else if (name == "MSS") {
            image_ids <- geojson$mss_id
        } else {
            stop("Nombre especificado no es válido")
        }

        # Crear ImageCollection a partir de los IDs de las imágenes
        images <- lapply(image_ids, ee$Image)
        image_collection <- ee$ImageCollection(images)

        # Obtener el metadato de cada imagen en la colección
        metadata_info <- image_collection$aggregate_array(meta)
        metadata_values <- metadata_info$getInfo()

        # Agregar la información del metadato como una nueva columna en geojson
        new_col_name <- paste0(name, "_", meta)
        geojson[[new_col_name]] <- metadata_values
    }
    # Escribir el geojson modificado a un archivo
    output_path <- paste0(dirname(geojson_path), "/", name, "_metadata_added.geojson")
    #write geojson if exist delete and write
    if (file.exists(output_path)) file.remove(output_path)
    st_write(geojson, output_path)
    return(geojson)
}

# Ejemplo de cómo llamar a la función:
# Reemplaza "geojson_path" con la ruta al archivo geojson en tu sistema
geojson_mod <- add_metadata_to_geojson(geojson_path = "D:/CURSOS_2022/Repos/AndesDataCube/Visualization/mss_tm.geojson",
                                       name = "TM",
                                       metadata = c("MAP_PROJECTION"))