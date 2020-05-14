function likelihood=get_likelihook_func(t)
home_path=getenv('ProgramData');
meas_data_path=strcat(home_path,'\Quantum_Lab\meas_data.mat');
load(meas_data_path);
temp=size(meas_data);
N=log2(temp(2));

base = ["I","X","X2p","Y2p"];
for qubit_idx=1:1:N
    op_idx=1;
    while op_idx<=4^N
        for base_gate_idx=1:1:4
            for repeat=1:1:(4^(N-qubit_idx))
                meas_pre_operation{op_idx,qubit_idx}=base(base_gate_idx);
                op_idx = op_idx+1;
            end
        end
    end
end

density_M=get_density(N,t);
likelihood=0;
for op_idx=1:1:4^N
    U=eye(2^N);
    for q_idx=1:1:N
        temp_U=get_U(N,q_idx,meas_pre_operation{op_idx,q_idx});
        U=temp_U*U;
    end
    temp = U*density_M;
    temp = temp*U';
    prob0_m = real(diag(temp));
    for p_idx=1:1:2^N
        likelihood = likelihood-meas_data(op_idx,p_idx)*log(prob0_m(p_idx));
    end
end
end