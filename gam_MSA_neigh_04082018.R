library(lfe)
library(data.table)
library(mgcv)
library(feather)
library(foreach)
library(mice)

#msa <-'10620'


# Create list of MSAs for which to run separate regressions
msa_list1 <- c('19300', '13820', '33660', '26620', '33860', '43420', '22380', '37740', '38060', '29420', '43320', '46060', '39140', '22220', '30780', '26300', '41860', '17020', '40900', '23420', '12540', '31080', '31460', '41500', '34900', '46020', '40140', '41940', '41740', '44700', '42020', '42200', '42100', '39820', '46700', '42220', '37100', '19740', '14500', '20780', '17820', '24060', '20420', '22660', '33940', '39380', '44460', '14720', '24540', '20100')
msa_list2 <- c('37980', '41540', '47900', '23540', '27260', '37460', '37340', '33100', '26140', '34940', '37860', '19660', '45220', '45300', '42680', '36740', '15980', '35840', '36100', '38940', '28580', '18880', '29460', '45540', '12260', '47580', '17980', '28180', '27980', '46520', '16980', '19340', '36860', '41180', '31140', '36540', '19780', '26980', '11180', '28140', '48620', '17140', '35380', '12580', '25180', '19820', '33460', '30700', '29820', '23820')
msa_list3 <- c('21220', '22280', '37220', '39900', '16180', '12100', '35620', '36140', '45940', '10900', '15380', '15500', '25860', '11700', '16740', '33980', '20500', '35100', '28620', '49180', '40580', '39580', '24660', '20380', '41820', '48900', '27340', '24780', '10620', '14380', '15940', '17460', '18140', '45780', '19380', '10420', '36420', '46140', '44660', '38900', '13460', '41420', '18700', '40700', '24420', '10540', '35440', '32780', '21660', '23900')
msa_list4 <- c('38300', '39740', '44300', '25420', '21500', '29540', '30140', '20700', '49620', '16700', '24860', '17900', '25940', '43900', '28940', '34980', '16860', '32820', '31260', '26420', '19100', '31180', '16820', '47260', '40220', '40060', '31340', '49020', '28420', '48300', '42660', '14740', '34580', '44060', '36500', '13380')

system.time(
  foo <- foreach(msa=msa_list1) %do% {                # doPar makes it run parallel, change to %do% for sequential loop
    # Load file
    path <- sprintf("G:\\Zillow\\Created\\MSAs\\transactions_%s.feather", msa)
    temp <- read_feather(path)
    # Format some columns as factors
    foo <- names(temp) %in% c('lprice'
                              , 'PropertyAddressLatitude'
                              , 'PropertyAddressLongitude'
                              , 'DocumentDate'
                              , 'ageAtSale'
                              , 'llota'
                              , 'lba'
                              , 'lgara'
                              , 'loba'
                              , 'tax_rate')
    
    discrete <- temp[!foo]
    temp[, c(names(discrete))] <- lapply(temp[, c(names(discrete))], factor)

    #Impute missing values
    predictors = quickpred(temp, mincor=0.2, minpuc=0.1)
    imputed <- mice(temp, m=1, maxit=1, predictorMatrix=predictors, method='norm.predict')
    temp = complete(imputed)  
    
    # OLS - HOA
    # Specify the formula (has to be flexible to allow for dropped variables in some MSAs)
    f <- as.formula(paste('lprice ~ hoa + ', paste(colnames(temp[, c(7:ncol(temp))]), collapse='+')))
    # Estimate the model
    model.OLS <- felm(formula=f, 
                      data=temp)
    summary_OLS <- summary(model.OLS)      
    # Save relevant statistics
    coef_HOA <- summary_OLS$coefficients[2,1]
    se_HOA   <- summary_OLS$coefficients[2,2]
    N <- summary_OLS$N
    # Save to a spreadsheet for later reference
    keep <- t(c("hoa_OLS", msa, coef_HOA, se_HOA, date(), N))
    write.table(keep, file = "G:/Zillow/Created/RegressionResults.csv", append=TRUE, sep = ",", col.names=FALSE, row.names=FALSE)
    
    
        # OLS - HOA_neigh
    # Specify the formula (has to be flexible to allow for dropped variables in some MSAs)
    f <- as.formula(paste('lprice ~ hoa_neigh + ', paste(colnames(temp[, c(7:ncol(temp))]), collapse='+')))
    # Estimate the model
    model.OLS <- felm(formula=f, 
                     data=temp,
                     subset=(hoa_neigh==0 | hoa_neigh==1))
    summary_OLS <- summary(model.OLS)      
    # Save relevant statistics
    coef_HOA <- summary_OLS$coefficients[2,1]
    se_HOA   <- summary_OLS$coefficients[2,2]
    N <- summary_OLS$N
    # Save to a spreadsheet for later reference
    keep <- t(c("hoa_neigh_OLS", msa, coef_HOA, se_HOA, date(), N))
    write.table(keep, file = "G:/Zillow/Created/RegressionResults.csv", append=TRUE, sep = ",", col.names=FALSE, row.names=FALSE)

    # Create an index of the non-numeric variables for each house, used in the GAM regression
    foo <- names(temp) %in% c('hoa'
                              , 'hoa_neigh'
                              , 'PropertyAddressLatitude'
                              , 'PropertyAddressLongitude'
                              , 'DocumentDate'
                              , 'ageAtSale'
                              , 'llota'
                              , 'lba'
                              , 'lgara'
                              , 'loba'
                              , 'tax_rate')
     
    cont <- names(temp) %in% c('hoa'
                               , 'hoa_neigh'
                               , 'PropertyAddressLatitude'
                               , 'PropertyAddressLongitude'
                               , 'DocumentDate'
                               , 'deed_type'
                               , 'ownerocc' 
                               , 'fireplace' 
                               , 'pool' 
                               , 'deck'                        
                               , 'bdrms'
                               , 'baths'
                               , 'topography'
                               , 'totrms'
                               , 'tile_rf'
                               , 'golf'
                               , 'waterfrnt'
                               , 'carpet_fl'
                               , 'wood_fl'
                               , 'extwall'
                               , 'fence')

    discrete <- temp[!foo]
    continuous <- temp[!cont]
    # Specify the formula (has to be flexible to allow for dropped variables in some MSAs)
    f <- as.formula(paste('lprice ~ ', 
                    paste(colnames(discrete[, c(3:ncol(discrete))]), collapse='+')))
    # Estimate a continuous index of discrete valued variables
    model.plm <- lm(formula=f, 
                     data=discrete)
    temp$index = predict(model.plm)

    
    # Run GAM on continuous variables, using the index
    continuous_demean <- demeanlist((continuous[, c(2:ncol(continuous))]), list(continuous$tract))
    continuous_demean$hoa = temp$hoa
    continuous_demean$hoa_neigh = temp$hoa_neigh
    continuous_demean$PropertyAddressLatitude = temp$PropertyAddressLatitude
    continuous_demean$PropertyAddressLongitude = temp$PropertyAddressLongitude
    continuous_demean$DocumentDate = temp$DocumentDate
    
    # GAM - HOA
    # Run GAM on continuous variables, using the index
    f <- as.formula(paste('lprice ~ hoa + s(DocumentDate) + s(', 
                          paste(colnames(continuous[, c(2:ncol(continuous))]), collapse=') + s('), 
                          paste(') + s(PropertyAddressLatitude, PropertyAddressLongitude)')))
    model.GAM <- bam(formula=f,
                     data=continuous_demean,
                     discrete=TRUE)
    summary_GAM <- summary(model.GAM)
    
    coef_HOA <- summary_GAM$p.table[2,1]
    se_HOA <- summary_GAM$p.table[2,2]
    N <- summary_GAM$n
    
    keep <- t(c("hoa_gam", msa, coef_HOA, se_HOA, date(), N))
    write.table(keep, file = "G:/Zillow/Created/RegressionResults.csv", append=TRUE, sep = ",", col.names=FALSE, row.names=FALSE)
    
    
        # GAM - HOA_neigh
    # Run GAM on continuous variables, using the index
    f <- as.formula(paste('lprice ~ hoa_neigh + s(DocumentDate) + s(', 
                          paste(colnames(continuous[, c(2:ncol(continuous))]), collapse=') + s('), 
                          paste(') + s(PropertyAddressLatitude, PropertyAddressLongitude)')))
    model.GAM <- bam(formula=f,
                     data=continuous_demean,
                     discrete=TRUE,
                     subset=(hoa_neigh==0 | hoa_neigh==1))
    summary_GAM <- summary(model.GAM)
    
    coef_HOA <- summary_GAM$p.table[2,1]
    se_HOA <- summary_GAM$p.table[2,2]
    N <- summary_GAM$n
    
    keep <- t(c("hoa_neigh_gam", msa, coef_HOA, se_HOA, date(), N))
    write.table(keep, file = "G:/Zillow/Created/RegressionResults.csv", append=TRUE, sep = ",", col.names=FALSE, row.names=FALSE)
  }
)
