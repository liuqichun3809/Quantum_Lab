function likelihood=get_likelihook_func(t)
N=2;
meas_pre_operation=["I","X","I","X2p","X2p","X2p","X2p","Y2p","Y2p","Y2p","Y2p","I", "X",  "I",  "X"; "I","I","X", "I", "X2p","Y2p", "X",  "I", "X2p","Y2p", "X","X2p","X2p","Y2p","Y2p"];
home_path=getenv('ProgramData');
meas_data_path=strcat(home_path,'\Quantum_Lab\meas_data.mat');
load(meas_data_path);

density_M=get_density(N,t);
likelihood=0;
for op_idx=1:1:15
    U=[1,0,0,0; 0,1,0,0; 0,0,1,0; 0,0,0,1];
    for q_idx=1:1:N
        temp_U=get_U(q_idx,meas_pre_operation(q_idx,op_idx));
        U=temp_U*U;
    end
    temp = U*density_M;
    temp = temp*U';
    prob0_m = real(diag(temp));
    for p_idx=1:1:4
        likelihood = likelihood-meas_data(op_idx,p_idx)*log(prob0_m(p_idx));
    end
end
end