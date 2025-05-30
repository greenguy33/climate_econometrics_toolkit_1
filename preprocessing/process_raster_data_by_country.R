# setwd("econometric_model_comparison/data")

library("exactextractr")
library("sf")
library("stringr")
library("raster")

# climate_vars = c("temp","precip","spec_humidity")
climate_vars = c("temp")
# timeframes = c("daily","monthly")
timeframes = c("daily")

country_shapes = read_sf("country_shapes",layer="country")
# pop_raster = raster("../data/gpw-v4-population-density-rev11_2000_30_sec_tif/gpw_v4_population_density_rev11_2000_30_sec.tif")
# ag_raster = raster("../data/CroplandPastureArea2000_Geotiff/Cropland2000_5m.tif")
soybean_raster = raster("crop_maps/harvested_area/soybean_HarvestedAreaFraction.tif")

single_climate_raster = stack(str_interp("../data/temp/daily/shifted/air.2m.gauss.1961.shifted.nc"))
# pop_raster <- resample(pop_raster, single_climate_raster)
# pop_raster[is.na(pop_raster)] <- 0
# ag_raster <- resample(ag_raster, single_climate_raster)
# ag_raster[is.na(ag_raster)] <- 0
soybean_raster <- resample(soybean_raster, single_climate_raster)
soybean_raster[is.na(soybean_raster)] <- 0


lapply(climate_vars, function(climate_var) {
  lapply(timeframes, function(timeframe) {
    files <- list.files(path=str_interp("../data/${climate_var}/${timeframe}/shifted/"))
    lapply(files, function(file) {
      
      year = strsplit(file, split = "\\.")[[1]][4]
      climate_raster = stack(str_interp("../data/${climate_var}/${timeframe}/shifted/${file}"))
      
      # unweighted_by_country = exact_extract(climate_raster, country_shapes, fun = "mean")
      # pop_weighted_by_country = exact_extract(climate_raster, country_shapes, fun = "weighted_mean", weights=pop_raster)
      # ag_weighted_by_country = exact_extract(climate_raster, country_shapes, fun = "weighted_mean", weights=ag_raster)
      soybeanweighted_by_country = exact_extract(climate_raster, country_shapes, fun = "weighted_mean", weights=soybean_raster)

      data <- c()
      data$country <- country_shapes$GMI_CNTRY
      data$soybeanweighted_by_country <- soybeanweighted_by_country
      write.csv(data, str_interp("../data/${climate_var}/${timeframe}/processed_by_country/soybean_weighted/${climate_var}.${timeframe}.bycountry.soybeanweighted.${year}.csv"))

      # data <- c()
      # data$country <- country_shapes$GMI_CNTRY
      # data$unweighted_by_country <- unweighted_by_country
      # write.csv(data, str_interp("../data/${climate_var}/${timeframe}/processed_by_country/unweighted/${climate_var}.${timeframe}.bycountry.unweighted.${year}.csv"))

      # data <- c()
      # data$country <- country_shapes$GMI_CNTRY
      # data$popweighted_by_country <- pop_weighted_by_country
      # write.csv(data, str_interp("../data/${climate_var}/${timeframe}/processed_by_country/popweighted/${climate_var}.${timeframe}.bycountry.popweighted.${year}.csv"))

      # data <- c()
      # data$country <- country_shapes$GMI_CNTRY
      # data$agweighted_by_country <- ag_weighted_by_country
      # write.csv(data, str_interp("../data/${climate_var}/${timeframe}/processed_by_country/agweighted/${climate_var}.${timeframe}.bycountry.agweighted.${year}.csv"))
    })
  })
})