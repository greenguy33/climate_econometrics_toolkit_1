import pandas as pd
import numpy as np
import statsmodels.api as sm
import copy
from statsmodels.tsa.statespace.tools import diff
import pyfixest as pf

import climate_econometrics_toolkit.model_builder as cet
import climate_econometrics_toolkit.regression as cer
import climate_econometrics_toolkit.utils as utils
import climate_econometrics_toolkit.interface_api as api


def get_data():
	datafile = "tests/test_data/GDP_climate_test_data.csv"
	data = pd.read_csv(datafile)
	return data, datafile

def test_simple_covariates():

	data = get_data()[0]
	from_indices = ['Temp', 'Precip']
	to_indices = ['GDP_per_capita', 'GDP_per_capita']
	model = cet.parse_model_input([from_indices, to_indices], get_data()[1], "iso_id", "year")[0]
	
	transformed_data = utils.transform_data(data, model)

	res1 = cer.run_standard_regression(transformed_data, model, "nonrobust").summary2().tables[1]
	assert not any(np.isnan(val) for val in res1["Coef."])
	
	model = api.run_model_analysis(data,"nonrobust",model,cv_folds=2)
	assert not np.isnan(model[0].out_sample_mse)
	assert not np.isnan(model[0].out_sample_mse_reduction)
	assert not np.isnan(model[0].in_sample_mse)
	assert not np.isnan(model[0].out_sample_pred_int_cov)
	assert .99 > model[0].out_sample_pred_int_cov and .92 < model[0].out_sample_pred_int_cov
	pd.testing.assert_frame_equal(res1.sort_index(), model[0].regression_result.summary2().tables[1].sort_index())

	covars = ["Precip", "Temp"]
	regression_data = data[covars]
	regression_data = sm.add_constant(regression_data)
	model = sm.OLS(data["GDP_per_capita"],regression_data,missing="drop")
	res2 = model.fit().summary2().tables[1]
	
	pd.testing.assert_frame_equal(res1.sort_index() ,res2.sort_index())

def test_transformed_target_simple_covariates():

	data = get_data()[0]
	from_indices = ['Temp', 'Precip']
	to_indices = ['fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))']
	model = cet.parse_model_input([from_indices, to_indices], get_data()[1], "iso_id", "year")[0]
	
	transformed_data = utils.transform_data(data, model)
	assert(all(val in transformed_data for val in ['ln(GDP_per_capita)','fd(ln(GDP_per_capita))']))
	
	res1 = cer.run_standard_regression(transformed_data, model, "nonrobust").summary2().tables[1]
	assert not any(np.isnan(val) for val in res1["Coef."])
	
	model = api.run_model_analysis(data,"nonrobust",model,cv_folds=2)
	assert not np.isnan(model[0].out_sample_mse)
	assert not np.isnan(model[0].out_sample_mse_reduction)
	assert not np.isnan(model[0].in_sample_mse)
	assert not np.isnan(model[0].out_sample_pred_int_cov)
	assert .99 > model[0].out_sample_pred_int_cov and .92 < model[0].out_sample_pred_int_cov
	pd.testing.assert_frame_equal(res1.sort_index(), model[0].regression_result.summary2().tables[1].sort_index())

	covars = ["Precip", "Temp"]
	regression_data = data[covars]
	regression_data = sm.add_constant(regression_data)
	data["ln(GDP_per_capita)"] = np.log(data["GDP_per_capita"])
	data["fd(ln(GDP_per_capita))"] = data.groupby("iso_id")["ln(GDP_per_capita)"].diff()
	model = sm.OLS(data["fd(ln(GDP_per_capita))"],regression_data,missing="drop")
	res2 = model.fit().summary2().tables[1]
	
	pd.testing.assert_frame_equal(res1.sort_index() ,res2.sort_index())

def test_2_transformed_covariates_transformed_target():

	data = get_data()[0]
	from_indices = ['ln(Precip)', 'sq(Precip)', 'Precip', 'Temp', 'sq(Temp)', 'fd(Temp)', 'ln(Temp)', 'fd(Precip)', 'lag1(Precip)', 'lag3(Temp)']
	to_indices = ['ln(fd(GDP_per_capita))', 'ln(fd(GDP_per_capita))', 'ln(fd(GDP_per_capita))', 'ln(fd(GDP_per_capita))', 'ln(fd(GDP_per_capita))', 'ln(fd(GDP_per_capita))', 'ln(fd(GDP_per_capita))', 'ln(fd(GDP_per_capita))','ln(fd(GDP_per_capita))', 'ln(fd(GDP_per_capita))']
	model = cet.parse_model_input([from_indices, to_indices], get_data()[1], "iso_id", "year")[0]
	
	transformed_data = utils.transform_data(data, model)
	assert(all(val in transformed_data for val in ['fd(GDP_per_capita)','ln(fd(GDP_per_capita))','sq(Temp)','fd(Temp)','ln(Temp)','sq(Precip)','fd(Precip)','ln(Precip)','lag1(Precip)','lag3(Temp)']))

	res1 = cer.run_standard_regression(transformed_data, model, "nonrobust").summary2().tables[1]
	assert not any(np.isnan(val) for val in res1["Coef."])

	model = api.run_model_analysis(data,"nonrobust",model,cv_folds=2)
	assert not np.isnan(model[0].out_sample_mse)
	assert not np.isnan(model[0].out_sample_mse_reduction)
	assert not np.isnan(model[0].in_sample_mse)
	assert not np.isnan(model[0].out_sample_pred_int_cov)
	assert .99 > model[0].out_sample_pred_int_cov and .92 < model[0].out_sample_pred_int_cov
	pd.testing.assert_frame_equal(res1.sort_index(), model[0].regression_result.summary2().tables[1].sort_index())

	covars = ["Precip", "Temp", "ln(Temp)", "ln(Precip)", "fd(Temp)", "fd(Precip)", "sq(Temp)", "sq(Precip)","lag1(Precip)","lag3(Temp)"]
	data["ln(Temp)"] = np.log(data["Temp"])
	data["ln(Precip)"] = np.log(data["Precip"])
	data["fd(Temp)"] = data.groupby("iso_id")["Temp"].diff()
	data["fd(Precip)"] = diff(data["Precip"])
	data["sq(Temp)"] = np.square(data["Temp"])
	data["sq(Precip)"] = np.square(data["Precip"])
	data["fd(GDP_per_capita)"] = data.groupby("iso_id")["GDP_per_capita"].diff()
	data["ln(fd(GDP_per_capita))"] = np.log(data["fd(GDP_per_capita)"])
	data["lag1(Precip)"] = data.groupby("iso_id")["Precip"].shift(1)
	data["lag3(Temp)"] = data.groupby("iso_id")["Temp"].shift(3)

	data = data.dropna(subset=["ln(fd(GDP_per_capita))"])

	regression_data = data[covars]
	regression_data = sm.add_constant(regression_data)
	model = sm.OLS(data["ln(fd(GDP_per_capita))"],regression_data,missing="drop")
	res2 = model.fit().summary2().tables[1]

	pd.testing.assert_frame_equal(res1.sort_index() ,res2.sort_index(), rtol=1e-04)

def test_transformed_covariates_transformed_target():

	data = get_data()[0]
	from_indices = ['ln(Precip)', 'sq(Precip)', 'Precip', 'Temp', 'sq(Temp)', 'fd(Temp)', 'ln(Temp)', 'fd(Precip)']
	to_indices = ['fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))']
	model = cet.parse_model_input([from_indices, to_indices], get_data()[1], "iso_id", "year")[0]
	
	transformed_data = utils.transform_data(data, model)
	assert(all(val in transformed_data for val in ['ln(GDP_per_capita)','fd(ln(GDP_per_capita))','sq(Temp)','fd(Temp)','ln(Temp)','sq(Precip)','fd(Precip)','ln(Precip)']))

	res1 = cer.run_standard_regression(transformed_data, model, "nonrobust").summary2().tables[1]
	assert not any(np.isnan(val) for val in res1["Coef."])

	model = api.run_model_analysis(data,"nonrobust",model,cv_folds=2)
	assert not np.isnan(model[0].out_sample_mse)
	assert not np.isnan(model[0].out_sample_mse_reduction)
	assert not np.isnan(model[0].in_sample_mse)
	assert not np.isnan(model[0].out_sample_pred_int_cov)
	assert .99 > model[0].out_sample_pred_int_cov and .92 < model[0].out_sample_pred_int_cov
	pd.testing.assert_frame_equal(res1.sort_index(), model[0].regression_result.summary2().tables[1].sort_index())

	covars = ["Precip", "Temp", "ln(Temp)", "ln(Precip)", "fd(Temp)", "fd(Precip)", "sq(Temp)", "sq(Precip)"]
	data["ln(Temp)"] = np.log(data["Temp"])
	data["ln(Precip)"] = np.log(data["Precip"])
	data["fd(Temp)"] = data.groupby("iso_id")["Temp"].diff()
	data["fd(Precip)"] = data.groupby("iso_id")["Precip"].diff()
	data["sq(Temp)"] = np.square(data["Temp"])
	data["sq(Precip)"] = np.square(data["Precip"])
	regression_data = data[covars]
	regression_data = sm.add_constant(regression_data)
	data["ln(GDP_per_capita)"] = np.log(data["GDP_per_capita"])
	data["fd(ln(GDP_per_capita))"] = data.groupby("iso_id")["ln(GDP_per_capita)"].diff()
	model = sm.OLS(data["fd(ln(GDP_per_capita))"],regression_data,missing="drop")
	res2 = model.fit().summary2().tables[1]

	pd.testing.assert_frame_equal(res1.sort_index() ,res2.sort_index())

def test_fe_transformed_covariates_transformed_target_iso_year_fixed_effects():

	data = get_data()[0]
	from_indices = ['fe(year)', 'fe(iso_id)', 'Temp', 'sq(Temp)', 'fd(Temp)', 'Precip', 'fd(Precip)', 'sq(Precip)']
	to_indices = ['fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))']
	model = cet.parse_model_input([from_indices, to_indices], get_data()[1], "iso_id", "year")[0]

	transformed_data = utils.transform_data(data, model)
	assert(all(val in transformed_data for val in ['ln(GDP_per_capita)','fd(ln(GDP_per_capita))','sq(Temp)','fd(Temp)','sq(Precip)','fd(Precip)','fe_AGO_iso_id','fe_1963_year']))

	res1 = cer.run_standard_regression(transformed_data, model, "nonrobust").summary2().tables[1]
	assert not any(np.isnan(val) for val in res1["Coef."])
	
	model = api.run_model_analysis(data,"nonrobust",model,cv_folds=2)
	assert not np.isnan(model[0].out_sample_mse)
	assert not np.isnan(model[0].out_sample_mse_reduction)
	assert not np.isnan(model[0].in_sample_mse)
	assert not np.isnan(model[0].out_sample_pred_int_cov)
	assert .99 > model[0].out_sample_pred_int_cov and .92 < model[0].out_sample_pred_int_cov

	res2 = model[0].regression_result.summary2().tables[1].sort_index()
	np.testing.assert_allclose(res1.loc['Temp']["Coef."],res2.loc['Temp']["Coef."],rtol=1e-04)
	np.testing.assert_allclose(res1.loc['Precip']["Coef."],res2.loc['Precip']["Coef."],rtol=1e-04)
	np.testing.assert_allclose(res1.loc['sq(Temp)']["Coef."],res2.loc['sq(Temp)']["Coef."],rtol=1e-04)
	np.testing.assert_allclose(res1.loc['sq(Precip)']["Coef."],res2.loc['sq(Precip)']["Coef."],rtol=1e-04)
	np.testing.assert_allclose(res1.loc['fd(Temp)']["Coef."],res2.loc['fd(Temp)']["Coef."],rtol=1e-04)
	np.testing.assert_allclose(res1.loc['fd(Precip)']["Coef."],res2.loc['fd(Precip)']["Coef."],rtol=1e-04)

	data["fd_temp"] = data.groupby("iso_id")["Temp"].diff()
	data["fd_precip"] = data.groupby("iso_id")["Precip"].diff()
	data["sq_temp"] = np.square(data["Temp"])
	data["sq_precip"] = np.square(data["Precip"])
	data["ln_gdp"] = np.log(data["GDP_per_capita"])
	data["fd_ln_gdp"] = data.groupby("iso_id")["ln_gdp"].diff()
	
	res3 = pf.feols("fd_ln_gdp ~ Temp + Precip + fd_temp + fd_precip + sq_temp + sq_precip | iso_id + year", data=data).coef()

	np.testing.assert_allclose(float(res1.loc[["Precip"]]["Coef."]),float(res3.loc[["Precip"]]),rtol=1e-04)
	np.testing.assert_allclose(float(res1.loc[["Temp"]]["Coef."]),float(res3.loc[["Temp"]]),rtol=1e-04)
	np.testing.assert_allclose(float(res1.loc[["sq(Precip)"]]["Coef."]),float(res3.loc[["sq_precip"]]),rtol=1e-04)
	np.testing.assert_allclose(float(res1.loc[["sq(Temp)"]]["Coef."]),float(res3.loc[["sq_temp"]]),rtol=1e-04)
	np.testing.assert_allclose(float(res1.loc[["fd(Precip)"]]["Coef."]),float(res3.loc[["fd_precip"]]),rtol=1e-04)
	np.testing.assert_allclose(float(res1.loc[["fd(Temp)"]]["Coef."]),float(res3.loc[["fd_temp"]]),rtol=1e-04)

def test_fe_transformed_covariates_transformed_target_iso_fixed_effect():

	data = get_data()[0]
	from_indices = ['fe(iso_id)', 'Temp', 'sq(Temp)', 'fd(Temp)', 'Precip', 'fd(Precip)', 'sq(Precip)']
	to_indices = ['fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))']
	model = cet.parse_model_input([from_indices, to_indices], get_data()[1], "iso_id", "year")[0]
	
	transformed_data = utils.transform_data(data, model)
	assert(all(val in transformed_data for val in ['ln(GDP_per_capita)','fd(ln(GDP_per_capita))','sq(Temp)','fd(Temp)','sq(Precip)','fd(Precip)','fe_AGO_iso_id']))

	res1 = cer.run_standard_regression(transformed_data, model, "nonrobust").summary2().tables[1]
	assert not any(np.isnan(val) for val in res1["Coef."])
	
	model = api.run_model_analysis(data,"nonrobust",model,cv_folds=2)
	assert not np.isnan(model[0].out_sample_mse)
	assert not np.isnan(model[0].out_sample_mse_reduction)
	assert not np.isnan(model[0].in_sample_mse)
	assert not np.isnan(model[0].out_sample_pred_int_cov)
	assert .99 > model[0].out_sample_pred_int_cov and .92 < model[0].out_sample_pred_int_cov

	res2 = model[0].regression_result.summary2().tables[1].sort_index()
	np.testing.assert_allclose(res1.loc['Temp']["Coef."],res2.loc['Temp']["Coef."],rtol=1e-04)
	np.testing.assert_allclose(res1.loc['Precip']["Coef."],res2.loc['Precip']["Coef."],rtol=1e-04)
	np.testing.assert_allclose(res1.loc['sq(Temp)']["Coef."],res2.loc['sq(Temp)']["Coef."],rtol=1e-04)
	np.testing.assert_allclose(res1.loc['sq(Precip)']["Coef."],res2.loc['sq(Precip)']["Coef."],rtol=1e-04)
	np.testing.assert_allclose(res1.loc['fd(Temp)']["Coef."],res2.loc['fd(Temp)']["Coef."],rtol=1e-04)
	np.testing.assert_allclose(res1.loc['fd(Precip)']["Coef."],res2.loc['fd(Precip)']["Coef."],rtol=1e-04)

	data["fd_temp"] = data.groupby("iso_id")["Temp"].diff()
	data["fd_precip"] = data.groupby("iso_id")["Precip"].diff()
	data["sq_temp"] = np.square(data["Temp"])
	data["sq_precip"] = np.square(data["Precip"])
	data["ln_gdp"] = np.log(data["GDP_per_capita"])
	data["fd_ln_gdp"] = data.groupby("iso_id")["ln_gdp"].diff()
	
	res3 = pf.feols("fd_ln_gdp ~ Temp + Precip + fd_temp + fd_precip + sq_temp + sq_precip | iso_id ", data=data).coef()

	np.testing.assert_allclose(float(res1.loc[["Precip"]]["Coef."]),float(res3.loc[["Precip"]]),rtol=1e-04)
	np.testing.assert_allclose(float(res1.loc[["Temp"]]["Coef."]),float(res3.loc[["Temp"]]),rtol=1e-04)
	np.testing.assert_allclose(float(res1.loc[["sq(Precip)"]]["Coef."]),float(res3.loc[["sq_precip"]]),rtol=1e-04)
	np.testing.assert_allclose(float(res1.loc[["sq(Temp)"]]["Coef."]),float(res3.loc[["sq_temp"]]),rtol=1e-04)
	np.testing.assert_allclose(float(res1.loc[["fd(Precip)"]]["Coef."]),float(res3.loc[["fd_precip"]]))
	np.testing.assert_allclose(float(res1.loc[["fd(Temp)"]]["Coef."]),float(res3.loc[["fd_temp"]]),rtol=1e-04)

def test_tt_transformed_covariates_transformed_target_time_trends():

	data = get_data()[0]
	from_indices = ['Temp', 'Precip', 'tt2(iso_id)']
	to_indices = ['ln(GDP_per_capita)', 'ln(GDP_per_capita)', 'ln(GDP_per_capita)']
	model = cet.parse_model_input([from_indices, to_indices], get_data()[1], "iso_id", "year")[0]
	
	transformed_data = utils.transform_data(data, model)
	transformed_data.to_csv("reg1.csv")
	assert(all(val in transformed_data for val in ['ln(GDP_per_capita)','Temp','Precip','tt1_AFG_iso_id','tt2_AFG_iso_id']))

	res1 = cer.run_standard_regression(transformed_data, model, "nonrobust").summary2().tables[1]
	assert not any(np.isnan(val) for val in res1["Coef."])

	model = api.run_model_analysis(data,"nonrobust",model,cv_folds=2)
	assert not np.isnan(model[0].out_sample_mse)
	assert not np.isnan(model[0].out_sample_mse_reduction)
	assert not np.isnan(model[0].in_sample_mse)
	assert not np.isnan(model[0].out_sample_pred_int_cov)
	assert .99 > model[0].out_sample_pred_int_cov and .92 < model[0].out_sample_pred_int_cov
	pd.testing.assert_frame_equal(res1.sort_index(), model[0].regression_result.summary2().tables[1].sort_index())

	tt_test_data = pd.read_csv("tests/test_data/time_trend_test_data.csv")
	tt_test_data["Temp"] = tt_test_data["UDel_temp_popweight"]
	tt_test_data["Precip"] = tt_test_data["UDel_precip_popweight"]
	
	tt_test_data["ln(GDP_per_capita)"] =  np.log(tt_test_data["gdpCAP_wdi"])

	climate_covars = ["Precip", "Temp"]
	covars = copy.deepcopy(climate_covars)
	covars.extend([col for col in tt_test_data.columns if col.startswith("_y")])
	regression_data = tt_test_data[covars]
	regression_data = sm.add_constant(regression_data)

	model = sm.OLS(tt_test_data["ln(GDP_per_capita)"],regression_data,missing="drop")
	res2 = model.fit().summary2().tables[1]

	assert len(res1) == len(res2)
	pd.testing.assert_frame_equal(res1.loc[climate_covars], res2.loc[climate_covars])

def test_tt_transformed_covariates_transformed_target_fixed_effects_and_time_trends():

	data = get_data()[0]
	from_indices = ['Temp', 'Precip', 'fd(Temp)', 'sq(Temp)', 'sq(Precip)', 'fd(Precip)', 'fe(year)', 'fe(iso_id)', 'tt2(iso_id)']
	to_indices = ['fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))']
	model = cet.parse_model_input([from_indices, to_indices], get_data()[1], "iso_id", "year")[0]
	
	transformed_data = utils.transform_data(data, model)
	assert(all(val in transformed_data for val in ['ln(GDP_per_capita)','fd(ln(GDP_per_capita))','sq(Temp)','fd(Temp)','sq(Precip)','fd(Precip)','fe_AGO_iso_id','fe_1963_year','tt1_AFG_iso_id','tt2_AFG_iso_id']))

	res1 = cer.run_standard_regression(transformed_data, model, "nonrobust").summary2().tables[1]
	assert not any(np.isnan(val) for val in res1["Coef."])

	model = api.run_model_analysis(data,"nonrobust",model,cv_folds=2)
	assert not np.isnan(model[0].out_sample_mse)
	assert not np.isnan(model[0].out_sample_mse_reduction)
	assert not np.isnan(model[0].in_sample_mse)
	assert not np.isnan(model[0].out_sample_pred_int_cov)
	assert .99 > model[0].out_sample_pred_int_cov and .92 < model[0].out_sample_pred_int_cov
	
	res2 = model[0].regression_result.summary2().tables[1]
	
	np.testing.assert_allclose(res1.loc['Temp']["Coef."],res2.loc['Temp']["Coef."],rtol=1e-04)
	np.testing.assert_allclose(res1.loc['Precip']["Coef."],res2.loc['Precip']["Coef."],rtol=1e-04)
	np.testing.assert_allclose(res1.loc['sq(Temp)']["Coef."],res2.loc['sq(Temp)']["Coef."],rtol=1e-04)
	np.testing.assert_allclose(res1.loc['sq(Precip)']["Coef."],res2.loc['sq(Precip)']["Coef."],rtol=1e-04)
	np.testing.assert_allclose(res1.loc['fd(Temp)']["Coef."],res2.loc['fd(Temp)']["Coef."],rtol=1e-04)
	np.testing.assert_allclose(res1.loc['fd(Precip)']["Coef."],res2.loc['fd(Precip)']["Coef."],rtol=1e-04)

	tt_test_data = pd.read_csv("tests/test_data/time_trend_test_data.csv")
	tt_test_data["Temp"] = tt_test_data["UDel_temp_popweight"]
	tt_test_data["Precip"] = tt_test_data["UDel_precip_popweight"]

	tt_test_data["fd_temp"] = data.groupby("iso_id")["Temp"].diff()
	tt_test_data["fd_precip"] = data.groupby("iso_id")["Precip"].diff()
	tt_test_data["sq_temp"] = np.square(tt_test_data["Temp"])
	tt_test_data["sq_precip"] =  np.square(tt_test_data["Precip"])
	tt_test_data["ln_gdp"] =  np.log(tt_test_data["gdpCAP_wdi"])
	tt_test_data["fd_ln_gdp"] =  tt_test_data.groupby("iso_id")["ln_gdp"].diff()

	climate_covars = ["Precip", "Temp", "fd_temp", "fd_precip", "sq_temp", "sq_precip"]
	covars = copy.deepcopy(climate_covars)
	covars.extend([col for col in tt_test_data.columns if col.startswith("_y")])
	covar_string = " + ".join(covars)

	res3 = pf.feols(f"fd_ln_gdp ~ {covar_string} | iso_id + year", data=tt_test_data).coef()

	np.testing.assert_allclose(float(res1.loc[["Precip"]]["Coef."]),float(res3.loc[["Precip"]]),rtol=1e-04)
	np.testing.assert_allclose(float(res1.loc[["Temp"]]["Coef."]),float(res3.loc[["Temp"]]),rtol=1e-04)
	np.testing.assert_allclose(float(res1.loc[["sq(Precip)"]]["Coef."]),float(res3.loc[["sq_precip"]]),rtol=1e-04)
	np.testing.assert_allclose(float(res1.loc[["sq(Temp)"]]["Coef."]),float(res3.loc[["sq_temp"]]),rtol=1e-04)
	np.testing.assert_allclose(float(res1.loc[["fd(Precip)"]]["Coef."]),float(res3.loc[["fd_precip"]]),rtol=1e-04)
	np.testing.assert_allclose(float(res1.loc[["fd(Temp)"]]["Coef."]),float(res3.loc[["fd_temp"]]),rtol=1e-04)

def test_burke_model():

	# test from original burke dataset

	from_indices = ['Temp', 'Precip', 'sq(Temp)', 'sq(Precip)','fe(year)', 'fe(iso_id)', 'tt2(iso_id)']
	to_indices = ['growthWDI', 'growthWDI', 'growthWDI', 'growthWDI', 'growthWDI', 'growthWDI', 'growthWDI', 'growthWDI', 'growthWDI']
	data = get_data()[0]
	model_input = cet.parse_model_input([from_indices, to_indices], get_data()[1], "iso_id", "year")[0]

	data["ln(GDP_per_capita)"] = np.log(data["GDP_per_capita"])
	data["fd(ln(GDP_per_capita))"] = data.groupby("iso_id")["ln(GDP_per_capita)"].diff()
	nan_indices = data[data["fd(ln(GDP_per_capita))"].isnull()].index
	test_data = data.drop(nan_indices).reset_index(drop=True)
	pd.testing.assert_series_equal(
		test_data["growthWDI"],
		test_data["fd(ln(GDP_per_capita))"],
		check_names = False,
		check_index = False,
		atol=1e-04,
		rtol=1e-04
	)

	utils.random_state = 123
	model = api.run_model_analysis(test_data, "nonrobust",model_input,cv_folds=25)
	assert .09 < model[0].out_sample_mse_reduction < .12
	assert .949 < model[0].out_sample_pred_int_cov < .952
	
	# TODO: random state 1 returns very different result
	utils.random_state = 1
	model = api.run_model_analysis(test_data, "nonrobust",model_input,cv_folds=25)
	print(model[0].out_sample_mse_reduction)
	assert .09 < model[0].out_sample_mse_reduction < .12
	assert .949 < model[0].out_sample_pred_int_cov < .952

	utils.random_state = 99
	model = api.run_model_analysis(data, "nonrobust",model_input,cv_folds=25)
	assert .09 < model[0].out_sample_mse_reduction < .12
	assert .949 < model[0].out_sample_pred_int_cov < .952


def test_ortiz_bobea_model():

	# test from original ortiz-bobea dataset

	datafile = "tests/test_data/ortiz_bobea_data.csv"
	data = pd.read_csv(datafile)

	# year fixed effects

	from_indices = ['fd_tmean', 'fd_prcp', 'fd_tmean_sq', 'fd_prcp_sq','fe(year)']
	to_indices = ['fd_log_tfp', 'fd_log_tfp', 'fd_log_tfp', 'fd_log_tfp', 'fd_log_tfp']
	model_input = cet.parse_model_input([from_indices, to_indices], datafile, "ISO3", "year")[0]

	# TODO: test transformations lead to same result

	utils.random_state = 123
	model = api.run_model_analysis(data,"nonrobust",model_input,cv_folds=2)
	assert .007 < model[0].out_sample_mse_reduction < .009
	assert .947 < model[0].out_sample_pred_int_cov < .950
	
	utils.random_state = 1
	model = api.run_model_analysis(data,"nonrobust",model_input,cv_folds=2)
	assert .007 < model[0].out_sample_mse_reduction < .009
	assert .947 < model[0].out_sample_pred_int_cov < .950

	utils.random_state = 99
	model = api.run_model_analysis(data,"nonrobust",model_input,cv_folds=2)
	assert .007 < model[0].out_sample_mse_reduction < .009
	assert .947 < model[0].out_sample_pred_int_cov < .950

	year_fe_red = model[0].out_sample_mse_reduction

	# country fixed effects

	from_indices = ['fd_tmean', 'fd_prcp', 'fd_tmean_sq', 'fd_prcp_sq', 'fe(ISO3)']
	to_indices = ['fd_log_tfp', 'fd_log_tfp', 'fd_log_tfp', 'fd_log_tfp', 'fd_log_tfp']
	model_input = cet.parse_model_input([from_indices, to_indices], datafile, "ISO3", "year")[0]

	# TODO: test transformations lead to same result

	utils.random_state = 123
	model = api.run_model_analysis(data,"nonrobust",model_input,cv_folds=2)
	assert .011 < model[0].out_sample_mse_reduction < .013
	assert .947 < model[0].out_sample_pred_int_cov < .950
	
	utils.random_state = 1
	model = api.run_model_analysis(data,"nonrobust",model_input,cv_folds=2)
	assert .011 < model[0].out_sample_mse_reduction < .013
	assert .947 < model[0].out_sample_pred_int_cov < .950

	utils.random_state = 99
	model = api.run_model_analysis(data,"nonrobust",model_input,cv_folds=2)
	assert .011 < model[0].out_sample_mse_reduction < .013
	assert .947 < model[0].out_sample_pred_int_cov < .950

	country_fe_red = model[0].out_sample_mse_reduction

	# both

	from_indices = ['fd_tmean', 'fd_prcp', 'fd_tmean_sq', 'fd_prcp_sq','fe(year)', 'fe(ISO3)']
	to_indices = ['fd_log_tfp', 'fd_log_tfp', 'fd_log_tfp', 'fd_log_tfp', 'fd_log_tfp', 'fd_log_tfp']
	model_input = cet.parse_model_input([from_indices, to_indices], datafile, "ISO3", "year")[0]

	# TODO: test transformations lead to same result

	utils.random_state = 123
	model = api.run_model_analysis(data,"nonrobust",model_input,cv_folds=2)
	assert .008 < model[0].out_sample_mse_reduction < .010
	assert .947 < model[0].out_sample_pred_int_cov < .950
	
	utils.random_state = 1
	model = api.run_model_analysis(data,"nonrobust",model_input,cv_folds=2)
	assert .008 < model[0].out_sample_mse_reduction < .010
	assert .947 < model[0].out_sample_pred_int_cov < .950

	utils.random_state = 99
	model = api.run_model_analysis(data,"nonrobust",model_input,cv_folds=2)
	assert .008 < model[0].out_sample_mse_reduction < .010
	assert .947 < model[0].out_sample_pred_int_cov < .950

	both_fe_red = model[0].out_sample_mse_reduction

	assert year_fe_red < both_fe_red
	assert both_fe_red < country_fe_red

def test_single_covariates_random_slopes():

	data = get_data()[0]
	from_indices = ['re(Temp)']
	to_indices = ['fd(ln(GDP_per_capita))']
	model = cet.parse_model_input([from_indices, to_indices], get_data()[1], "iso_id", "year")[0]

	try:
		api.run_model_analysis(data,"nonrobust",model)
	except AssertionError as e:
		assert str(e) == "No model covariates found. Please update your model."

def test_multiple_covariates_random_slopes():

	data = get_data()[0]
	from_indices = ['Precip', 'fd(Temp)', 'sq(Temp)', 'sq(Precip)', 'fd(Precip)', 're(Temp)']
	to_indices = ['fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))']
	model = cet.parse_model_input([from_indices, to_indices], get_data()[1], "iso_id", "year")[0]
	transformed_data = utils.transform_data(data, model)
	assert(all(val in transformed_data for val in ['ln(GDP_per_capita)','fd(ln(GDP_per_capita))','sq(Temp)','fd(Temp)','sq(Precip)','fd(Precip)']))

	res1 = cer.run_random_effects_regression(transformed_data, model).params
	assert not any(np.isnan(val) for val in res1)

	model = api.run_model_analysis(data,"nonrobust",model,cv_folds=2)
	assert not np.isnan(model[0].out_sample_mse)
	assert not np.isnan(model[0].out_sample_mse_reduction)
	assert not np.isnan(model[0].in_sample_mse)
	assert np.isnan(model[0].out_sample_pred_int_cov)
	assert not np.isnan(model[0].rmse)
	pd.testing.assert_series_equal(res1.sort_index(), model[0].regression_result.params.sort_index())

def test_fixed_intercepts_with_random_slopes():

	data = get_data()[0]
	from_indices = ['Precip', 'fd(Temp)', 'sq(Temp)', 'sq(Precip)', 'fd(Precip)', 're(Temp)', 'fe(iso_id)']
	to_indices = ['fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))']
	model = cet.parse_model_input([from_indices, to_indices], get_data()[1], "iso_id", "year")[0]
	transformed_data = utils.transform_data(data, model)
	assert(all(val in transformed_data for val in ['ln(GDP_per_capita)','fd(ln(GDP_per_capita))','sq(Temp)','fd(Temp)','sq(Precip)','fd(Precip)','fe_AGO_iso_id']))

	res1 = cer.run_random_effects_regression(transformed_data, model).params
	assert not any(np.isnan(val) for val in res1)

	model = api.run_model_analysis(data,"nonrobust",model,cv_folds=2)
	assert not np.isnan(model[0].out_sample_mse)
	assert not np.isnan(model[0].out_sample_mse_reduction)
	assert not np.isnan(model[0].in_sample_mse)
	assert np.isnan(model[0].out_sample_pred_int_cov)
	assert not np.isnan(model[0].rmse)
	pd.testing.assert_series_equal(res1.sort_index(), model[0].regression_result.params.sort_index())

def test_time_trends_with_random_slopes():

	data = get_data()[0]
	from_indices = ['Precip', 'fd(Temp)', 'sq(Temp)', 'sq(Precip)', 'fd(Precip)', 're(Temp)', 'tt2(iso_id)']
	to_indices = ['fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))', 'fd(ln(GDP_per_capita))']
	model = cet.parse_model_input([from_indices, to_indices], get_data()[1], "iso_id", "year")[0]

	try:
		api.run_model_analysis(data,"nonrobust",model)
	except AssertionError as e:
		assert str(e) == "Time trends and random effects cannot currently be combined in a single model. Please update your model."
