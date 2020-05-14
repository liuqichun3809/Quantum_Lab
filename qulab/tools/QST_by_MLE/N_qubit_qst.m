clear all;
close all;

home_path=getenv('ProgramData');
meas_data_path=strcat(home_path,'\Quantum_Lab\meas_data.mat');
load(meas_data_path);

temp=size(meas_data);
N=log2(temp(2));

t=rand(4^N,1);
L=get_likelihook_func(t);
likelihood = @get_likelihook_func;
OPTIONS = optimset('MaxFunEvals',max_evals,'MaxIter',max_evals,'TolFun',1e-8,'TolX',1e-5,'PlotFcns',@optimplotfval);
[t_MLE,L_MLE,exitflag,output] = fminsearch(likelihood,t,OPTIONS);

rho = get_density(N,t_MLE);
result_data_path=strcat(home_path,'\Quantum_Lab\MLE_result.mat')
save(result_data_path,'rho')
