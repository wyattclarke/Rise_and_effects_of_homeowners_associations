library(plm)
library(data.table)
library(mgcv)
library(feather)
library(mice)
library(lfe)


# Load list of transactions, with missing values imputed
Main <- read_feather("G:\\Zillow\\Created\\transactions.feather")

# Optionally, store to avoid reloading and subset to run faster
store <- Main
Main <- store

Main <- Main[Main$DataClassStndCode=="H", ]
Main$DataClassStndCode <- NULL
Main <- Main[Main$DocumentDate>=16425, ]

#Main <- Main[sample(nrow(Main), 60000),]

divisions <- read.csv('G:\\Zillow\\Created\\division_state_xwalk.csv')
Main$state_code <- paste("G", substr(Main$FIPS,1,2), sep="")
Main <- merge(Main, divisions,  by="state_code", all.x=TRUE, all.y=FALSE)




Main$hoa_neigh <- replace(Main$hoa_neigh, is.na(Main$hoa_neigh), 10)
Main$YearBuilt_mode <- replace(Main$YearBuilt_mode, is.na(Main$YearBuilt_mode), 10)
Main$baths <- replace(Main$baths, is.na(Main$baths), 0)
Main$topography <- replace(Main$topography, is.na(Main$topography), 'other')
Main$deed_type <- factor(Main$deed_type)
Main$tract <- factor(Main$tract)
Main$pool <- factor(Main$pool)
Main$deck <- factor(Main$deck)
Main$bdrms <- factor(Main$bdrms)
Main$baths <- factor(Main$baths)
Main$topography <- factor(Main$topography)
Main$totrms <- factor(Main$totrms)
Main$tile_rf <- factor(Main$tile_rf)
Main$golf <- factor(Main$golf)
Main$waterfrnt <- factor(Main$waterfrnt)
Main$carpet_fl <- factor(Main$carpet_fl)
Main$wood_fl <- factor(Main$wood_fl)
Main$extwall <- factor(Main$extwall)
Main$fence <- factor(Main$fence)
Main$hoa <- factor(Main$hoa)
Main$hoa_neigh <- factor(Main$hoa_neigh)

# Recode to limit unnecessary factors


#Impute remaining missing values
predictors = quickpred(Main, mincor=0.2, minpuc=0.1)
imputed <- mice(Main, m=1, maxit=1, predictorMatrix=predictors, method='norm.predict')
Main = complete(imputed)  

division='G3'
for (division in c('G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9')){
  # GAM
  temp <- Main[Main$division_code==division,]
  # Estimate a continuous index of discrete valued variables
  model.lm <- lm(data=temp,
                 formula = lprice ~                         
                   deed_type +
                   ownerocc + 
                   fireplace + 
                   pool + 
                   deck +                        
                   bdrms +
                   baths+
                   topography +
                   totrms +
                   tile_rf +
                   #golf +
                   waterfrnt +
                   carpet_fl +
                   wood_fl +
                   extwall +
                   fence)
  temp$index <- predict(model.lm)
  
  temp2 <- demeanlist((temp[, c('index', 'lprice', 'llota', 'lba', 'lgara', 'loba', 'ageAtSale', 'tax_rate')]), list(temp$tract))
  temp2$hoa = temp$hoa
  temp2$PropertyAddressLatitude = temp$PropertyAddressLatitude
  temp2$PropertyAddressLongitude = temp$PropertyAddressLongitude
  temp2$DocumentDate = temp$DocumentDate
  
  system.time(
    model.GAM <- bam(data=temp2,
                     discrete=TRUE,
                     nthreads=4,
                     lprice ~ 
                       hoa +
                       s(index) +
                       s(llota) +
                       s(lba) +
                       s(lgara) +
                       s(loba) +
                       s(DocumentDate) + 
                       s(ageAtSale) + 
                       s(tax_rate) + 
                       s(PropertyAddressLatitude, PropertyAddressLongitude)))
  regional_result <- summary(model.GAM)
  cat(paste(division), capture.output(regional_result), file='G:\\Zillow\\Created\\RegresssionResults\\store6.txt', sep="n", append=TRUE)
}
