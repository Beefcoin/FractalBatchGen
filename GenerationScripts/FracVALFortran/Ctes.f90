!here i changed everything from compile time consts to runtime variables 
!the arrays were set to allocatable, to be dependend on variable N
!the initialization subroutine was added

module Ctes
    implicit none

    integer :: N = 500                            ! Number of PP
    real :: Df = 2.4                              ! Fractal dimension
    real :: kf = 0.8                              ! Fractal prefactor
    real :: rp_g = 1.00                           ! Geometric mean PP
    real :: rp_gstd = 1.00                        ! Geometric PP standard deviation
    integer :: Quantity_aggregates = 1            ! Quantity of aggregates to be generated
    integer :: Ext_case = 0                       ! Activate extreme cases
    real :: Nsubcl_perc = 0.1                     ! Controls the subclusters size
    real :: tol_ov = 10.**(-6.)                   ! Tolerance to overlapping

    real, parameter :: pi = 4.0 * atan(1.0)

    real, allocatable :: R(:)                     ! Primary particles radii
    real, allocatable :: X(:), Y(:), Z(:)         ! Coordinates of primary particles

    integer :: iter, i, j, k

contains
    !initialization subrouztine
    subroutine init_ctes(N_in, Df_in, kf_in, rp_g_in, rp_gstd_in, &
                         Quantity_aggregates_in, Ext_case_in, &
                         Nsubcl_perc_in, tol_ov_in)
        implicit none

        !set all variables to their corresponding inputs from the warpper
        integer, intent(in) :: N_in
        real, intent(in) :: Df_in, kf_in
        real, intent(in) :: rp_g_in, rp_gstd_in
        integer, intent(in) :: Quantity_aggregates_in, Ext_case_in
        real, intent(in) :: Nsubcl_perc_in, tol_ov_in

        N = N_in
        Df = Df_in
        kf = kf_in
        rp_g = rp_g_in
        rp_gstd = rp_gstd_in
        Quantity_aggregates = Quantity_aggregates_in
        Ext_case = Ext_case_in
        Nsubcl_perc = Nsubcl_perc_in
        tol_ov = tol_ov_in

        !cleanup so we dont memory leak 
        if (allocated(R)) deallocate(R)
        if (allocated(X)) deallocate(X)
        if (allocated(Y)) deallocate(Y)
        if (allocated(Z)) deallocate(Z)

        allocate(R(N))
        allocate(X(N))
        allocate(Y(N))
        allocate(Z(N))

        !initialize everything to starting values
        R = 0.0
        X = 0.0
        Y = 0.0
        Z = 0.0

        iter = 0
        i = 0
        j = 0
        k = 0
    end subroutine init_ctes

    !set seed for reproducability
    subroutine set_seed(seed_in)
        implicit none
        integer, intent(in) :: seed_in
        integer :: n, i
        integer, allocatable :: seed(:)

        call random_seed(size=n)
        allocate(seed(n))

        do i = 1, n
            seed(i) = seed_in + 37 * (i - 1)
        end do

        call random_seed(put=seed)

        deallocate(seed)
    end subroutine set_seed

end module Ctes
