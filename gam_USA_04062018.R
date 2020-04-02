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

#Main <- Main[Main$DataClassStndCode=="H", ]
#Main$DataClassStndCode <- NULL
Main <- Main[Main$DocumentDate>=16425, ]

Main <- Main[sample(nrow(Main), 60000),]



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

# OLS
system.time(  
  model.OLS <- felm(data=Main,
                    lprice ~ hoa +
                       lba +
                       llota +
                       lgara +
                       loba +
                       DocumentDate + 
                       ageAtSale +
                       tax_rate + 
                       deed_type +
                       ownerocc + 
                       fireplace + 
                       pool + 
                       deck +                        
                       bdrms +
                       baths +
                       topography +
                       totrms +
                       tile_rf +
                       golf +
                       waterfrnt +
                       carpet_fl +
                       wood_fl +
                       extwall +
                       fence |
                      tract)) 
store1 <- summary(model.OLS) 

model.OLS <- felm(data=Main,                      
                  subset=(hoa_neigh==0 | hoa_neigh==1),
                  lprice ~ hoa +
                   lba +
                   llota +
                   lgara +
                   loba +
                   DocumentDate + 
                   ageAtSale +
                   tax_rate + 
                   deed_type +
                   ownerocc + 
                   fireplace + 
                   pool + 
                   deck +                        
                   bdrms +
                   baths +
                   topography +
                   totrms +
                   tile_rf +
                   golf +
                   waterfrnt +
                   carpet_fl +
                   wood_fl +
                   extwall +
                   fence |
                   tract)
store2 <- summary(model.OLS)

model.OLS <- felm(data=Main,                      
                  subset=(hoa_neigh==0 | hoa_neigh==1),
                  lprice ~ hoa_neigh +
                    lba +
                    llota +
                    lgara +
                    loba +
                    DocumentDate + 
                    ageAtSale +
                    tax_rate + 
                    deed_type +
                    ownerocc + 
                    fireplace + 
                    pool + 
                    deck +                        
                    bdrms +
                    baths +
                    topography +
                    totrms +
                    tile_rf +
                    golf +
                    waterfrnt +
                    carpet_fl +
                    wood_fl +
                    extwall +
                    fence |
                    tract)
store3 <- summary(model.OLS)

# GAM
# Estimate a continuous index of discrete valued variables
model.lm <- lm(data=Main, 
               formula = lprice ~                         
                 deed_type +
                 ownerocc + 
                 fireplace + 
                 pool + 
                 deck +                        
                 bdrms +
                 baths +
                 topography +
                 totrms +
                 tile_rf +
                 golf +
                 waterfrnt +
                 carpet_fl +
                 wood_fl +
                 extwall +
                 fence)
Main$index = predict(model.lm)

temp <- demeanlist((Main[, c('index', 'lprice', 'llota', 'lba', 'lgara', 'loba', 'ageAtSale', 'tax_rate')]), list(Main$tract))
temp$hoa = Main$hoa
temp$PropertyAddressLatitude = Main$PropertyAddressLatitude
temp$PropertyAddressLongitude = Main$PropertyAddressLongitude
temp$DocumentDate = Main$DocumentDate

system.time(
  model.GAM <- bam(data=temp,
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
store4 <- summary(model.GAM)

# Estimate a continuous index of discrete valued variables
Main_sm <- Main[(Main$hoa_neigh==1 | Main$hoa_neigh==0), ]
model.lm <- lm(data=Main_sm, 
                formula = lprice ~                         
                   deed_type +
                   ownerocc + 
                   fireplace + 
                   pool + 
                   deck +                        
                   bdrms +
                   baths +
                   topography +
                   totrms +
                   tile_rf +
                   golf +
                   waterfrnt +
                   carpet_fl +
                   wood_fl +
                   extwall +
                   fence)
Main_sm$index = predict(model.lm)

temp <- demeanlist((Main_sm[, c('index', 'lprice', 'llota', 'lba', 'lgara', 'loba', 'ageAtSale', 'tax_rate')]), list(Main_sm$tract))
temp$hoa = Main_sm$hoa
temp$hoa_neigh = Main_sm$hoa_neigh
temp$PropertyAddressLatitude = Main_sm$PropertyAddressLatitude
temp$PropertyAddressLongitude = Main_sm$PropertyAddressLongitude
temp$DocumentDate = Main_sm$DocumentDate

system.time(
  model.GAM <- bam(data=temp,
                   discrete=TRUE,
                   nthreads=4,
                   lprice ~ hoa +
                     s(index) +
                     s(llota) +
                     s(lba) +
                     s(lgara) +
                     s(loba) +
                     s(DocumentDate) + 
                     s(ageAtSale) + 
                     s(tax_rate) + 
                     s(PropertyAddressLatitude, PropertyAddressLongitude)))
store5 <- summary(model.GAM)

system.time(
  model.GAM <- bam(data=temp,
                   discrete=TRUE,
                   nthreads=4,
                   lprice ~ hoa_neigh +
                     s(index) +
                     s(llota) +
                     s(lba) +
                     s(lgara) +
                     s(loba) +
                     s(DocumentDate) + 
                     s(ageAtSale) + 
                     s(tax_rate) + 
                     s(PropertyAddressLatitude, PropertyAddressLongitude)))
store6 <- summary(model.GAM)
cat("store6", capture.output(store6), file='G:\\Zillow\\Created\\RegresssionResults\\store6.txt', sep="n", append=TRUE)


