function U=get_U(N,qubit_idx,pre_op)
I=[1,0;0,1];
X2p=[1/sqrt(2),-sqrt(-1)/sqrt(2); -sqrt(-1)/sqrt(2),1/sqrt(2)];
X=[0,-sqrt(-1); -sqrt(-1),0];
Y2p=[1/sqrt(2),-1/sqrt(2); 1/sqrt(2),1/sqrt(2)];

if pre_op=='I'
    U=I;
end

if pre_op=='X'
    U=X;
end

if pre_op=='X2p'
    U=X2p;
end

if pre_op=='Y2p'
    U=Y2p;
end

for idx=1:1:(N-qubit_idx)
    U = kron(I,U);
end

for idx=1:1:qubit_idx-1
    U = kron(U,I);
end

end