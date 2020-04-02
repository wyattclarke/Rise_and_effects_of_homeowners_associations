library(feather)    # Reading and writing data
library(data.table) # fread function

###################################################
# Load spreadsheet of regression coefficients
df <- fread("G:/Zillow/Created/RegressionResults_old.csv", 
              header=FALSE, 
              col.names=c('regtype', 'cbsacode', 'coef', 'se', 'datetime', 'N'))
df[ , regtype!='hoa_gam'] = NULL
df <- subset(df, regtype=='hoa_gam')
df = df[!duplicated(df$cbsacode),]


# Reformat variables
df$coef <- as.numeric(df$coef)
df$se <- as.numeric(df$se)
df$N <- as.numeric(df$N)
df$regtype <- as.factor(df$regtype)

###################################################
# LOAD AND MERGE SUPPORTING DATA SETS
# Census characteristics pulled from American Factfinder
census <- read_feather("G:/Zillow/SupportingDataSets/CensusChars/chars.feather")
# Match to coefs using MSA codes
df <- merge(df, census, by="cbsacode", all.x=TRUE, all.y=FALSE)

# MSA-level descriptive statistics of parcels from Zillow
housing <- read_feather('G:/Zillow/Created/descriptive_statistics_msa.feather')
df <- merge(df, housing, by="cbsacode", all.x=TRUE, all.y=FALSE)

# GINI indices from Census
  # Load
gini <- fread("G:/Zillow/SupportingDataSets/MSAGiniCoefs_Census/ACS_10_5YR_B19083_with_ann.csv",
              select=c(2,3,4),
              header=FALSE,
              col.names=c('cbsacode', 'msaname', 'gini'))
  # Isolate MSA city and state for matching
gini$gini <- as.numeric(gini$gini) #NAs introduced warning is OK
gini$msacity <- gsub( ",.*$", "", gini$msaname)
gini$msacity <- gsub( "-.*$", "", gini$msacity)
gini$msastate <- gsub(".*, ", "", gini$msaname)
gini$msastate <- gsub(" .*$", "", gini$msastate)
gini$msastate <- gsub( "-.*$", "", gini$msastate)
gini <- subset(gini, select=-msaname)
  # Match to coefs using MSA codes
df <- merge(df, gini, by="cbsacode", all.x=TRUE, all.y=FALSE)

# Racial biases from Project Implicit
  # Load
iat = read_feather("G:/Zillow/SupportingDataSets/IAT/iat_MSAmean.feather")
  # Isolate MSA city and state for matching
iat$msacity <- gsub( ",.*$", "", iat$msaname)
iat$msacity <- gsub( "-.*$", "", iat$msacity)
iat$msacity <- gsub('Sarasota', 'North Port', iat$msacity)
iat$msastate <- gsub(".*, ", "", iat$msaname)
iat$msastate <- gsub(" .*$", "", iat$msastate)
iat$msastate <- gsub( "-.*$", "", iat$msastate)
iat <- subset(iat, select=-msaname)
  # Match to coefs using MSA city and state
df <- merge(df, iat, by=c("msacity", "msastate"), all.x=TRUE, all.y=FALSE)
  
# Wharton Residential Land Use Regulation Index by Gyourko et al
  # Load
zoning = fread("G:/Zillow/SupportingDataSets/ZoningRatings_Gyourko/Gyourko_MSAWeightedAvg.csv")
  # Isolate MSA city and state for matching
zoning$msacity <- gsub( ",.*$", "", zoning$msaname99)
zoning$msacity <- gsub( "-.*$", "", zoning$msacity)
zoning$msastate <- gsub(".*, ", "", zoning$msaname)
zoning$msastate <- gsub(" .*$", "", zoning$msastate)
zoning$msastate <- gsub( "-.*$", "", zoning$msastate)
zoning <- subset(zoning, select=-msaname99)
zoning <- subset(zoning, select=-msa99)
  # Match to coefs using MSA city and state
df <- merge(df, zoning, by=c("msacity", "msastate"), all.x=TRUE, all.y=FALSE)

###################################################
# Model MSA-level HOA premium heterogeneity
chars = c(colnames(df[, c(10:28)]))
for (char in chars){
  f <- paste('coef ~ ', char)
  record <- summary(lm(f, data=df, subset=(regtype=='hoa_gam')))
  # Save relevant statistics
  coef <- record$coefficients[2,1]
  se   <- record$coefficients[2,2]
  N <- record$df[2] + 2
  # Save to a spreadsheet for later reference
  keep <- t(c(char, coef, se, date(), N))
  write.table(keep, file = "G:/Zillow/Created/ComparingMSAs.csv", append=TRUE, sep = ",", col.names=FALSE, row.names=FALSE)
}

xwalk <- fread('G:\\Zillow\\cbsa2fipsxw2.csv')
xwalk <- xwalk[, c('cbsacode', 'statename')]

df <- df[,character(df$regtype)=='hoa_gam']
df <- merge(df, xwalk, by='cbsacode', all.x=TRUE, all.y=FALSE)

df$state <- substr(df$FIPS, 1, 2)

f <- as.formula(paste('coef ~', paste(chars, collapse='+')))
summary(lm(f, data=df, subset=(regtype=='hoa_gam')))
