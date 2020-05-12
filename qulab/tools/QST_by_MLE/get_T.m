function [MT,MTc]=get_T(N,t)
MT=zeros(2^N,2^N);
MTc=zeros(2^N,2^N);
tc=t;
for idx=1:1:4^N
    temp_idx = idx-1;
    row = floor(sqrt(temp_idx));
    col = floor((temp_idx-(row)^2)/2);
    if mod((temp_idx-row^2),2) == 1
        t(idx) = sqrt(-1)*t(idx);
        tc(idx) = -sqrt(-1)*tc(idx);
    end
    MT(row+1,col+1)= MT(row+1,col+1)+t(idx);
    MTc(col+1,row+1)= MTc(col+1,row+1)+tc(idx);
end