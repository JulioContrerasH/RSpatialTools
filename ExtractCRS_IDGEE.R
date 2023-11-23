library(sf)
library(rgee)
library(rgeeExtra)

ee_Initialize()
extra_Initialize()

table <- read.csv("D:/CURSOS_2022/Repos/RSpatialTools/dataset/metadata2.csv")
table$CRS <- NA
total_rows <- nrow(table)
batch_size <- 1000

for (start_row in seq(1, total_rows, by = batch_size)) {
  end_row <- min(start_row + batch_size - 1, total_rows)
  ic_ids <- table$IMG_ID[start_row:end_row]

  ic <- ee$ImageCollection(ic_ids) %>%
    ee$ImageCollection$map(
      function(img) {
        crs <- img$select("R")$projection()$crs()
        img$set(list("crs" = crs))
      }
    )

  crs_info <- ic$aggregate_array("crs")$getInfo()
  table$CRS[start_row:end_row] <- crs_info

  print(start_row)
}

write.csv(table, "D:/CURSOS_2022/Repos/RSpatialTools/dataset/metadata2_updated.csv", row.names = FALSE)
