#delimit ;
set more off;
clear;
/*********************************
* Program Name: HOA.do
* Authors: Wyatt Clarke/Matt Freedman
* Paper: Rise and Effects of HOAs
*********************************/
* Log;
	capture log close;
	log using HOA_USA.txt, text replace;

* Input Data;	
	use transactions_imputed_clusters, clear;
	keep if DocumentDate>=16425 & DataClassStndCode==2;
	keep if hoa_neigh~=4;

* Block Group Codes;
	sort RowID;
	merge m:1 RowID using all_SF_parcels;
	keep if _merge==1 | _merge==3;
	drop _merge;
	gen geoid=substr(PropertyAddressCenssTrctAndBlck,1,2)+substr(PropertyAddressCenssTrctAndBlck,3,3)+substr(PropertyAddressCenssTrctAndBlck,6,4)+substr(PropertyAddressCenssTrctAndBlck,11,3);
	drop PropertyAddressGeoCodeMatchCode PropertyLandUseStndCode YearBuilt mortgage county state;
	compress;

* Create Variables for USA Regression;
	gen HOA=(hoa==2);
	gen HOA_NEIGH=(hoa_neigh==2);
	replace HOA_NEIGH=. if hoa_neigh==9 | hoa_neigh==3;
	gen foreclosure=(deed_type==1);
	gen warranty=(deed_type==3);
	tab bdrms, gen(bdrms_);
	tab baths, gen(baths_);
	tab totrms, gen(totrms_);
	tab topography, gen(topography_);
	gen extwall_brick=(extwall==2);
	gen extwall_siding=(extwall==5);
	gen extwall_stucco=(extwall==6);
	gen extwall_wood=(extwall==7);
* Approximate subdiv size;
	sort FIPS LegalSubdivisionName;
	by FIPS LegalSubdivisionName: gen c=_n;
	by FIPS LegalSubdivisionName: egen subdiv_size=max(c);
	drop c;
	replace subdiv_size=. if LegalSubdivisionName=="NA" | LegalSubdivisionName=="";

format DocumentDate %td;
gen year=year(DocumentDate);
gen mo=month(DocumentDate);
gen month=ym(year,mo);
format %tm month;

gen SS=substr(FIPS,1,2);

/* Descriptive Statistics;
	sort geoid;
	by geoid: egen HOA_geoid=mean(HOA);
	by geoid: egen HOA_NEIGH_geoid=mean(HOA_NEIGH);
	by geoid: gen bbbb=_n;
	sum HOA_geoid if bbbb==1, det;
	sum HOA_NEIGH_geoid if bbbb==1, det;
	unique SS;
	unique SS if HOA_geoid>0;
	unique SS if HOA_geoid>0 & HOA_geoid<1;
	unique cbsacode;
	unique cbsacode if HOA_geoid>0;
	unique cbsacode if HOA_geoid>0 & HOA_geoid<1;
	unique FIPS;
	unique FIPS if HOA_geoid>0;
	unique FIPS if HOA_geoid>0 & HOA_geoid<1;
	unique tract;
	unique tract if HOA_geoid>0;
	unique tract if HOA_geoid>0 & HOA_geoid<1;
	sort tract;
	by tract: egen HOA_tract=mean(HOA);
	by tract: egen HOA_NEIGH_tract=mean(HOA_NEIGH);
	by tract: gen tttttt=_n;
	sum HOA_tract if tttttt==1, det;
	sum HOA_NEIGH_tract if tttttt==1, det;
	unique SS;
	unique SS if HOA_tract>0;
	unique SS if HOA_tract>0 & HOA_tract<1;
	unique cbsacode;
	unique cbsacode if HOA_tract>0;
	unique cbsacode if HOA_tract>0 & HOA_tract<1;
	unique FIPS;
	unique FIPS if HOA_tract>0;
	unique FIPS if HOA_tract>0 & HOA_tract<1;
	*twoway (kdensity HOA_tract if tttttt==1) (kdensity HOA_NEIGH_tract if tttttt==1),
		legend(label(1 HOA by House) label(2 HOA by Neighborhood) col(1) region(style(none))) xtitle(Fraction of Tract in HOA) ytitle(Density)
		saving(HOA_Tract_Share.gph, replace);
		#delimit ;
	sort FIPS;
	by FIPS: egen HOA_county=mean(HOA);
	by FIPS: egen HOA_NEIGH_county=mean(HOA_NEIGH);
	by FIPS: gen ccc=_n;
	sum HOA_county if ccc==1, det;
	sum HOA_NEIGH_county if ccc==1, det;
	unique SS;
	unique SS if HOA_county>0;
	unique SS if HOA_county>0 & HOA_county<1;
	unique cbsacode;
	unique cbsacode if HOA_county>0;
	unique cbsacode if HOA_county>0 & HOA_county<1;
	*twoway (kdensity HOA_county if ccc==1) (kdensity HOA_NEIGH_county if ccc==1),
		legend(label(1 HOA by House) label(2 HOA by Neighborhood) col(1) region(style(none))) xtitle(Fraction of County in HOA) ytitle(Density)
		saving(HOA_County_Share.gph, replace);
*/

* Merge in All Data at County, CBSA, and State Levels for Interactions;	

	* Merge in WRLUR (CBSA);
	sort cbsacode;
	merge m:1 cbsacode using CBSA\CBSA_WRLURI;
	drop if _merge==2;
	drop _merge;
	
	* Merge in CBSA Chars;
	sort cbsacode;
	merge m:1 cbsacode using CBSA\CBSA_Characteristics;
	drop if _merge==2;
	drop _merge;
	sort cbsacode;
	merge m:1 cbsacode using CBSA\chars;
	drop if _merge==2;
	drop _merge;
	
	* Merge in IAT and Gini;
	sort cbsacode;
	merge m:1 cbsacode using CBSA\CBSA_Gini_IAT;
	drop if _merge==2;
	drop _merge;
		
	* Racial Integration Measures (GSS);
		*race_integration is a composite of several GSS questions of 1974-88. higher is more racially tolerant;
		*https://www.jstor.org/stable/3088421 - Taken from Brace, Sims-Butler, Arceneaux and Hohnson (2002);
	#delimit ;
	sort SS;
	merge m:1 SS using GSS\GSS_RaceIntegration;
		* note that zscore is z-score;
	drop if _merge==2;
	drop _merge;

	* Census of Governments Measures - all from 2012;
	sort FIPS;
	merge m:1 FIPS using CensusGovernments\CensusGovernments_County;
	drop if _merge==2;
	drop _merge;
	
qui tab month, gen(month_);	
egen tract_x_month=group(tract month);
egen geoid_x_month=group(geoid month);
destring geoid, gen(bg);

save HOA_USA_BASE, replace;
log close;	
	
**** National Regression Results ****;
set more off;
use HOA_USA_BASE, clear;
log using HOA_USA_Regs.txt, text replace;

**** Table 5 ****;
* 1. Cluster on County (FIPS);
* 2. Include Month-Year Dummies ;
* 3. Tract FEs and Tract-Month FEs;
areg lprice HOA lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
			bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
			extwall_brick extwall_siding 
			lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
			topography_1-topography_10 wood_fl extwall_stucco extwall_wood month_*, 
			absorb(tract) cluster(FIPS);
	est store main1;
areg lprice HOA lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
			bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
			extwall_brick extwall_siding 
			lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
			topography_1-topography_10 wood_fl extwall_stucco extwall_wood month_*, 
			absorb(tract_x_month) cluster(FIPS);
	est store main2;
areg lprice HOA_NEIGH lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
			bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
			extwall_brick extwall_siding 
			lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
			topography_1-topography_10 wood_fl extwall_stucco extwall_wood month_* if HOA_NEIGH<=1,
			absorb(tract) cluster(FIPS);
	est store main3;
areg lprice HOA_NEIGH lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
			bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
			extwall_brick extwall_siding 
			lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
			topography_1-topography_10 wood_fl extwall_stucco extwall_wood, 
			absorb(tract_x_month) cluster(FIPS);
	est store main4;
estout main?, cells(b(star fmt(3)) se(par(( )) fmt(3))) starlevels(* 0.10 ** 0.05 *** 0.01) stats(N);
est clear;

**** Robustness for Table 5 ****;
* 1. Cluster on County (FIPS);
* 2. Include Month-Year Dummies Instead of Continuous DocumentDate Variable;
* 3. BG FEs and BG-Month FEs;
areg lprice HOA lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
			bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
			extwall_brick extwall_siding 
			lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
			topography_1-topography_10 wood_fl extwall_stucco extwall_wood month_*, 
			absorb(geoid) cluster(FIPS);
	est store bg1;
areg lprice HOA lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
			bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
			extwall_brick extwall_siding 
			lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
			topography_1-topography_10 wood_fl extwall_stucco extwall_wood month_*, 
			absorb(geoid_x_month) cluster(FIPS);
	est store bg2;	
areg lprice HOA_NEIGH lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
			bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
			extwall_brick extwall_siding 
			lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
			topography_1-topography_10 wood_fl extwall_stucco extwall_wood month_*, 
			absorb(geoid) cluster(FIPS);
	est store bg3;
areg lprice HOA_NEIGH lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
			bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
			extwall_brick extwall_siding 
			lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
			topography_1-topography_10 wood_fl extwall_stucco extwall_wood, 
			absorb(geoid_x_month) cluster(FIPS);
	est store bg4;
estout bg?, cells(b(star fmt(3)) se(par(( )) fmt(3))) starlevels(* 0.10 ** 0.05 *** 0.01) stats(N);
est clear;

log close;

***** Tests for Influence of Unobservables (Oster 2017) ***;
set more off;
use HOA_USA_BASE, clear;
log using HOA_USA_Oster.txt, text replace;
forv i=1(1)145 {;
	local months `months' month_`i';
};
forv i=1(1)10 {;
	local topo `topo' topography_`i';
};
xtreg lprice HOA lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
			bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
			extwall_brick extwall_siding 
			lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
			topography_1-topography_10 wood_fl extwall_stucco extwall_wood month_*, 
			fe i(bg);
	est store robust2_x;
local rmaximum=1.3*e(r2_w);
psacalc delta HOA, mcontrol(`months') rmax(`rmaximum');
psacalc delta HOA, mcontrol(ageAtSale tax_rate foreclosure warranty ownerocc waterfrnt golf `topo' `months') rmax(`rmaximum');

xtreg lprice HOA_NEIGH lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
			bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
			extwall_brick extwall_siding 
			lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
			topography_1-topography_10 wood_fl extwall_stucco extwall_wood month_*, 
			fe i(bg);
	est store robust2_xn;
local rmaximum=1.3*e(r2_w);
psacalc delta HOA_NEIGH, mcontrol(`months') rmax(`rmaximum');
psacalc delta HOA_NEIGH, mcontrol(ageAtSale tax_rate foreclosure warranty ownerocc waterfrnt golf `topo' `months') rmax(`rmaximum');
log close;

***** Results by State ***;
* first set with sparser block group and month specification;
#delimit ;
set more off;
use HOA_USA_BASE, clear;
log using HOA_USA_States.txt, text replace;
levelsof SS, local(states);
capture gen state_hoa_obs=.;
capture gen state_hoa_beta=.;
capture gen state_hoa_ub=.;
capture gen state_hoa_lb=.;
qui {;
	foreach ss in `states' {;
		noisily di "State FIPS `ss'";
		count if SS=="`ss'";
		replace state_hoa_obs=r(N) if SS=="`ss'";
		local state_obs=r(N);
		capture areg lprice HOA lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
				bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
				extwall_brick extwall_siding 
				lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
				topography_1-topography_10 wood_fl extwall_stucco extwall_wood month_* if SS=="`ss'", 
				absorb(geoid) cluster(FIPS);
		if _rc==0 {; 
			capture replace state_hoa_beta=_b[HOA] if SS=="`ss'";
			capture replace state_hoa_ub=_b[HOA] + _se[HOA]*1.96 if SS=="`ss'";
			capture replace state_hoa_lb=_b[HOA] - _se[HOA]*1.96 if SS=="`ss'";
		};
		else if _rc!=0 noisily di as txt "    Insufficient observations (`state_obs') for State FIPS `ss'"; 
	};
};
sort SS;
by SS: gen s_n=_n;
by SS: egen state_hoa_share=mean(HOA);
merge m:1 SS using CensusRegionsDivisions;
drop if _merge==2;drop _merge;
tab region;

keep if s_n==1;
save HOA_USA_States, replace;

#delimit ;
local min_state_obs=1000;
pwcorr state_hoa_beta state_hoa_share if s_n==1 & state_hoa_obs>=`min_state_obs', sig;
twoway (scatter state_hoa_beta state_hoa_share if s_n==1 & region==1 & state_hoa_obs>=`min_state_obs', mcolor(red) ) 
	   (scatter state_hoa_beta state_hoa_share if s_n==1 & region==2 & state_hoa_obs>=`min_state_obs', mcolor(blue)) 
	   (scatter state_hoa_beta state_hoa_share if s_n==1 & region==3 & state_hoa_obs>=`min_state_obs', mcolor(green)) 
	   (scatter state_hoa_beta state_hoa_share if s_n==1 & region==4 & state_hoa_obs>=`min_state_obs', mcolor(yellow)) 
	   (lfit state_hoa_beta state_hoa_share if s_n==1 & state_hoa_obs>=`min_state_obs', lpattern(dash) lcolor(black) lwidth(medthin)), 
	legend(order(1 "Northeast" 2 "Midwest" 3 "South" 4 "West") region(style(none))) xtitle(State Share HOA) ytitle(HOA Premium);
pwcorr state_hoa_beta race_integration if s_n==1, sig;
twoway (scatter state_hoa_beta race_integration if s_n==1 & region==1 & state_hoa_obs>=`min_state_obs', mcolor(red) ) 
	   (scatter state_hoa_beta race_integration if s_n==1 & region==2 & state_hoa_obs>=`min_state_obs', mcolor(blue)) 
	   (scatter state_hoa_beta race_integration if s_n==1 & region==3 & state_hoa_obs>=`min_state_obs', mcolor(green)) 
	   (scatter state_hoa_beta race_integration if s_n==1 & region==4 & state_hoa_obs>=`min_state_obs', mcolor(yellow)) 
	   (lfit state_hoa_beta race_integration if s_n==1 & state_hoa_obs>=`min_state_obs', lpattern(dash) lcolor(black) lwidth(medthin)), 
	legend(order(1 "Northeast" 2 "Midwest" 3 "South" 4 "West") region(style(none))) xtitle(Racial Integration Index) ytitle(HOA Premium);

log close;
clear;

* second with richer BG x month FEs;
#delimit ;
set more off;
use HOA_USA_BASE, clear;
log using HOA_USA_xStates.txt, text replace;
levelsof SS, local(states);
capture gen state_hoa_obs=.;
capture gen state_hoa_beta=.;
capture gen state_hoa_ub=.;
capture gen state_hoa_lb=.;
qui {;
	foreach ss in `states' {;
		noisily di "State FIPS `ss'";
		count if SS=="`ss'";
		replace state_hoa_obs=r(N) if SS=="`ss'";
		local state_obs=r(N);
		areg lprice HOA lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
				bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
				extwall_brick extwall_siding 
				lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
				topography_1-topography_10 wood_fl extwall_stucco extwall_wood if SS=="`ss'", 
				absorb(geoid_x_month);
		if _rc==0 {; 
			capture replace state_hoa_beta=_b[HOA] if SS=="`ss'";
			capture replace state_hoa_ub=_b[HOA] + _se[HOA]*1.96 if SS=="`ss'";
			capture replace state_hoa_lb=_b[HOA] - _se[HOA]*1.96 if SS=="`ss'";
		};
		else if _rc!=0 noisily di as txt "    Insufficient observations (`state_obs') for State FIPS `ss'"; 
	};
};
sort SS;
by SS: gen s_n=_n;
by SS: egen state_hoa_share=mean(HOA);
merge m:1 SS using CensusRegionsDivisions;
drop if _merge==2;drop _merge;
tab region;

keep if s_n==1;
save HOA_USA_xStates, replace;

#delimit ;
local min_state_obs=500;
pwcorr state_hoa_beta state_hoa_share if s_n==1 & state_hoa_obs>=`min_state_obs', sig;
twoway (scatter state_hoa_beta state_hoa_share if s_n==1 & region==1 & state_hoa_obs>=`min_state_obs', mcolor(red) ) 
	   (scatter state_hoa_beta state_hoa_share if s_n==1 & region==2 & state_hoa_obs>=`min_state_obs', mcolor(blue)) 
	   (scatter state_hoa_beta state_hoa_share if s_n==1 & region==3 & state_hoa_obs>=`min_state_obs', mcolor(green)) 
	   (scatter state_hoa_beta state_hoa_share if s_n==1 & region==4 & state_hoa_obs>=`min_state_obs', mcolor(yellow)) 
	   (lfit state_hoa_beta state_hoa_share if s_n==1 & state_hoa_obs>=`min_state_obs', lpattern(dash) lcolor(black) lwidth(medthin)), 
	legend(order(1 "Northeast" 2 "Midwest" 3 "South" 4 "West") region(style(none))) xtitle(State Share HOA) ytitle(HOA Premium) saving(HOA_USA_xStates.gph, replace);
pwcorr state_hoa_beta race_integration if s_n==1, sig;
twoway (scatter race_integration state_hoa_beta if s_n==1) (lfit race_integration state_hoa_beta if s_n==1);
log close;
clear;


***** Results by MSA ***;
 * First using sparser specification with BG and month FEs;
#delimit ;
set more off;
use HOA_USA_BASE, clear;
log using HOA_USA_MSAs.txt, text replace;
levelsof cbsacode, local(cbsas);
gen cbsa_hoa_obs=.;
gen cbsa_hoa_beta=.;
gen cbsa_hoa_se=.;
gen cbsa_hoa_ub=.;
gen cbsa_hoa_lb=.;
qui {;
	foreach cbsa in `cbsas' {;
		noisily di "CBSA `cbsa'";
		count if cbsacode=="`cbsa'";
		replace cbsa_hoa_obs=r(N) if cbsacode=="`cbsa'";
		local cbsa_obs=r(N);
		capture areg lprice HOA lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
				bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
				extwall_brick extwall_siding 
				lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
				topography_1-topography_10 wood_fl extwall_stucco extwall_wood month_* if cbsacode=="`cbsa'", 
				absorb(geoid);
		if _rc==0 {; 
			capture replace cbsa_hoa_beta=_b[HOA] if cbsacode=="`cbsa'";
			capture replace cbsa_hoa_se=_se[HOA] if cbsacode=="`cbsa'";
			capture replace cbsa_hoa_ub=_b[HOA] + _se[HOA]*1.96 if cbsacode=="`cbsa'";
			capture replace cbsa_hoa_lb=_b[HOA] - _se[HOA]*1.96 if cbsacode=="`cbsa'";
		};
		else if _rc!=0 noisily di as txt "    Insufficient observations (`cbsa_obs') for CBSA `cbsa'"; 
	};
};
local min_cbsa_obs=10;
sort cbsacode;
by cbsacode: gen c_n=_n;
by cbsacode: egen cbsa_hoa_share=mean(HOA);

l cbsa* if cbsacode=="24540" & c_n==1;* Greeley, CO;
l cbsa* if cbsacode=="41180" & c_n==1;* St. Louis, MO;

keep if c_n==1;
compress;
save HOA_USA_MSAs, replace;
log close;
clear;

 * Second using richer specifications with BG x month FEs;
set more off;
use HOA_USA_BASE, clear;
log using HOA_USA_xMSAs.txt, text replace;
levelsof cbsacode, local(cbsas);
gen cbsa_hoa_obs=.;
gen cbsa_hoa_beta=.;
gen cbsa_hoa_se=.;
gen cbsa_hoa_ub=.;
gen cbsa_hoa_lb=.;
qui {;
	foreach cbsa in `cbsas' {;
		noisily di "CBSA `cbsa'";
		count if cbsacode=="`cbsa'";
		replace cbsa_hoa_obs=r(N) if cbsacode=="`cbsa'";
		local cbsa_obs=r(N);
		capture areg lprice HOA lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
				bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
				extwall_brick extwall_siding 
				lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
				topography_1-topography_10 wood_fl extwall_stucco extwall_wood if cbsacode=="`cbsa'", 
				absorb(geoid_x_month);
		if _rc==0 {; 
			capture replace cbsa_hoa_beta=_b[HOA] if cbsacode=="`cbsa'";
			capture replace cbsa_hoa_se=_se[HOA] if cbsacode=="`cbsa'";
			capture replace cbsa_hoa_ub=_b[HOA] + _se[HOA]*1.96 if cbsacode=="`cbsa'";
			capture replace cbsa_hoa_lb=_b[HOA] - _se[HOA]*1.96 if cbsacode=="`cbsa'";
		};
		else if _rc!=0 noisily di as txt "    Insufficient observations (`cbsa_obs') for CBSA `cbsa'"; 
	};
};
local min_cbsa_obs=10;
sort cbsacode;
by cbsacode: gen c_n=_n;
by cbsacode: egen cbsa_hoa_share=mean(HOA);

l cbsa* if cbsacode=="24540" & c_n==1;* Greeley, CO;
l cbsa* if cbsacode=="41180" & c_n==1;* St. Louis, MO;

keep if c_n==1;
compress;
save HOA_USA_xMSAs, replace;
log close;
clear;


**** Hetero Effects by Prop Characteristics ****;
set more off;
use HOA_USA_BASE, clear;
log using HOA_USA_HeteroEffects.txt, text replace;
gen HOA_x_ageAtSale=HOA*ageAtSale;
gen age14plus=(ageAtSale>=14);
gen age5under=(ageAtSale<5);
gen HOA_x_age14plus=HOA*(age14plus);
gen HOA_x_age5under=HOA*(age5under);
foreach v in tax_rate lba llota {;
	zscore `v';
	gen HOA_x_z_`v'=HOA*z_`v';
};
gen HOA_x_subdiv_size=HOA*subdiv_size;
gen subdiv_50plus=(subdiv_size>=50);
	replace subdiv_50plus=. if subdiv_size==.;
gen HOA_x_subdiv_50plus=HOA*subdiv_50plus;

foreach interaction in ageAtSale age14plus age5under z_lba z_llota z_tax_rate subdiv_size subdiv_50plus {;

	areg lprice HOA HOA_x_`interaction' lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
			bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
			extwall_brick extwall_siding 
			lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
			topography_1-topography_10 wood_fl extwall_stucco extwall_wood month_*, 
			absorb(geoid) cluster(FIPS);
};

log close;

/*

***** Interactions to Disentangle Mechanisms ***;
	
	gen ln_medianvalue=ln(medianvalue);
	destring gini, replace;
	gen property_tax_shr=property_tax_revenue/tax_revenue;
	foreach v in educ pubwelfare highways police parksrec admin {;
		rename general_expend_`v' expend_`v';
		gen `v'_expend_shr=expend_`v'/general_expend;
	};
	
	* Per-capita (100K county residents) measure;
	foreach v in total_revenue general_revenue tax_revenue property_tax_revenue total_expend general_expend expend_educ expend_pubwelfare expend_highways expend_police expend_parksrec expend_admin {;
		gen `v'_pc=ln(`v'/(population_county/100000));
	};
	gen ln_total_revenue=ln(total_revenue);
	gen ln_general_revenue=ln(general_revenue);
	gen ln_tax_revenue=ln(tax_revenue);
	gen ln_total_expend=ln(total_expend);
	gen ln_general_expend=ln(general_expend);

	foreach i in wrluri ln_medianvalue poverty YearBuilt_msa white_pref gini race_integration_zscore ln_general_revenue ln_tax_revenue property_tax_shr ln_general_expend educ_expend_shr pubwelfare_expend_shr highways_expend_shr police_expend_shr parksrec_expend_shr admin_expend_shr {;
		
		gen HOA_x_`i'=HOA*`i';
		gen HOA_N_x_`i'=HOA_NEIGH*`i';
	};
	foreach i in total_revenue general_revenue tax_revenue property_tax_revenue total_expend general_expend expend_educ expend_pubwelfare expend_highways expend_police expend_parksrec expend_admin {;
		gen HOA_x_`i'_pc=HOA*`i'_pc;
		gen HOA_N_x_`i'_pc=HOA_NEIGH*`i'_pc;
	};

	foreach i in wrluri ln_medianvalue poverty YearBuilt_msa white_pref gini race_integration_zscore{;
		di as txt "Interaction: `i'";
		areg lprice HOA HOA_x_`i' lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
				bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
				extwall_brick extwall_siding 
				lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
				topography_1-topography_10 wood_fl extwall_stucco extwall_wood month_*, 
				absorb(tract) cluster(FIPS);
			est store i_`i';
		areg lprice HOA_NEIGH HOA_N_x_`i' lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
				bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
				extwall_brick extwall_siding 
				lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
				topography_1-topography_10 wood_fl extwall_stucco extwall_wood month_*, 
				absorb(tract) cluster(FIPS);
			est store in_`i';
	};
	estout i_*, cells(b(star fmt(3)) se(par(( )) fmt(3))) starlevels(* 0.10 ** 0.05 *** 0.01) stats(N);
	estout in_*, cells(b(star fmt(3)) se(par(( )) fmt(3))) starlevels(* 0.10 ** 0.05 *** 0.01) stats(N);
	est clear;

	foreach i in ln_tax_revenue property_tax_shr educ_expend_shr pubwelfare_expend_shr highways_expend_shr police_expend_shr parksrec_expend_shr admin_expend_shr {;
		di as txt "Interaction: `i'";
		areg lprice HOA HOA_x_`i' lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
				bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
				extwall_brick extwall_siding 
				lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
				topography_1-topography_10 wood_fl extwall_stucco extwall_wood month_*, 
				absorb(tract) cluster(FIPS);
			est store i_`i';
		areg lprice HOA_NEIGH HOA_N_x_`i' lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
				bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
				extwall_brick extwall_siding 
				lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
				topography_1-topography_10 wood_fl extwall_stucco extwall_wood month_*, 
				absorb(tract) cluster(FIPS);
			est store in_`i';
	};
	estout i_*, cells(b(star fmt(3)) se(par(( )) fmt(3))) starlevels(* 0.10 ** 0.05 *** 0.01) stats(N);
	estout in_*, cells(b(star fmt(3)) se(par(( )) fmt(3))) starlevels(* 0.10 ** 0.05 *** 0.01) stats(N);
	est clear;

	foreach i in tax_revenue property_tax_revenue total_expend general_expend expend_educ expend_pubwelfare expend_highways expend_police expend_parksrec expend_admin {;
		di as txt "Per Capita Regressions - Interaction: `i'";
		areg lprice HOA HOA_x_`i'_pc lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
				bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
				extwall_brick extwall_siding 
				lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
				topography_1-topography_10 wood_fl extwall_stucco extwall_wood month_*, 
				absorb(tract) cluster(FIPS);
			est store i_`i';
		areg lprice HOA_NEIGH HOA_N_x_`i'_pc lba llota ageAtSale tax_rate foreclosure warranty ownerocc 
				bdrms_2 bdrms_3 bdrms_4 bdrms_5 bdrms_6 bdrms_7 pool waterfrnt carpet_fl 
				extwall_brick extwall_siding 
				lgara loba fireplace deck tile_rf fence golf baths_1-baths_10 totrms_1-totrms_10
				topography_1-topography_10 wood_fl extwall_stucco extwall_wood month_*, 
				absorb(tract) cluster(FIPS);
			est store in_`i';
	};
	estout i_*, cells(b(star fmt(3)) se(par(( )) fmt(3))) starlevels(* 0.10 ** 0.05 *** 0.01) stats(N);
	estout in_*, cells(b(star fmt(3)) se(par(( )) fmt(3))) starlevels(* 0.10 ** 0.05 *** 0.01) stats(N);
	est clear;	
	
	
	
log close;