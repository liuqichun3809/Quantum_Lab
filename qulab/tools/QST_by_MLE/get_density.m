function density_M=get_density(N,t)
[MT,MTc]=get_T(N,t);
density_M=MT*MTc;
density_M=density_M/trace(density_M);
end