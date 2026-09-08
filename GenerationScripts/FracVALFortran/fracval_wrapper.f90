!this is a python wrapper built around the original FracVAL Fortran Implementation (https://dx.doi.org/10.17632/mgf8wdcsfb.1)
!this is basically a simple interface that can directly be called from Python using f2py
!   1.Initialize all FracVAL global Parameters (N, Df, kf, rp_g, rp_gstd, tol_ov)
!   2.Generate random primary particle radiuses
!   3.Runs CCA aggregation algorithm
!   4.returns particle coords and radii to python
!        coords(:,1) -> x positions
!        coords(:,2) -> y positions
!        coords(:,3) -> z positions
!        radii(:)    -> particle radii

! I had to modify a lot of the FracVAL source because most variables were not allocatable and N was fixed during compilation (Data and almost everything in Ctes.f90)
! The following Files were modifieds:
! Ctes.f90
! CCA_module.f90

! I also implemented a set seed for reproducability in Ctes.f90


module fracval_wrapper

    !global simulation params and arrays
    use Ctes

    !radnom lognormal particle generation
    use a_Random_PP

    !random shuffling of particle radii
    use RAND_SAMPLE

    !main cca algorithm
    use CCA_module

    implicit none
contains

!This is the main wrapper, thats callable from python
!Inputs:
! N_in
! Df_in
! kf_in
! rp_g_in
! rp_gstd_in
! tol_ov_in
! seed_in
!
!Outputs:
! coords(:,1) -> x positions
! coords(:,2) -> y positions
! coords(:,3) -> z positions
! radii(:)    -> particle radii

!It can be called like this from python
! coords, radii, failed = fracval.fracval_wrapper.run_fracval(
!     500, 2.4, 0.8, 1.0, 1.0, 1e-6, 420
! )


subroutine run_fracval( &
    N_in, Df_in, kf_in, rp_g_in, rp_gstd_in, tol_ov_in, seed_in, &
    coords, radii, failed)

    implicit none


    !input params
    integer, intent(in) :: N_in
    real, intent(in) :: Df_in
    real, intent(in) :: kf_in
    real, intent(in) :: rp_g_in
    real, intent(in) :: rp_gstd_in
    real, intent(in) :: tol_ov_in
    integer, intent(in) :: seed_in

    !output arrays
    !particle coords
    real, intent(out) :: coords(N_in,3)

    !particle radii
    real, intent(out) :: radii(N_in)

    !success flag
    logical, intent(out) :: failed

    !internal error flags from FracVAL
    logical :: not_able_cca
    logical :: not_able_pca

    !init global fracVAL params
    call init_ctes( &
        N_in, &
        Df_in, &
        kf_in, &
        rp_g_in, &
        rp_gstd_in, &
        1, &          !generate 1 aggregate
        0, &          !disable extreme aggregation cases (idk what this does tbh)
        0.1, &        !subcluster percentage (standard from FracVAL)
        tol_ov_in)

    !init internal failure flags
    not_able_cca = .false.
    not_able_pca = .false.

    !aggregate counter used by fracval code internally
    iter = 1

    !call set_seed
    call set_seed(seed_in)

    !generate random primary particle radii, this is only used for polydisperse aggregates
    R = lognormal_pp_radii(rp_gstd, rp_g, N)
    !randomly shuffle generated radii
    R = randsample(R, N)


    !call the CCA subroutine
    call CCA_sub(not_able_cca, not_able_pca)

    !check internal failure flags -> for output failed
    failed = not_able_cca .or. not_able_pca

    !copy fracval internal arrays from module Ctes to the corresponding output arays
    coords(:,1) = X
    coords(:,2) = Y
    coords(:,3) = Z

    radii(:) = R

end subroutine run_fracval

end module fracval_wrapper
