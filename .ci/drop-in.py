print_summary(
    xas_demo_async(panda1, None, npoints=10_000, total_time=1, start_e=10, end_e=190)
)
(uid,) = RE(
    xas_demo_async(panda1, None, npoints=10_000, total_time=1, start_e=10, end_e=190)
)
print(uid)
