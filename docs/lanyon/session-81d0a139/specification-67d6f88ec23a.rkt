
#lang racket

(define transient-heat-diffusion-1d
  (hash
   'name "transient-heat-diffusion-1d"
   'coordinates (list `x)
   'state (list `u)
   'state-assumptions (list)
   'parameters (list `alpha)
   'parameters-assumptions (list `(> alpha 0.0))
   'fluxes (list
            (list 0.0))
   'wavespeeds (list
                (list 0.0))
   'diffusive-fluxes (list
                      (list `(* alpha u_x)))
   'sources (list 0.0)
   'source-speeds (list 0.0)
   )
  )

(define lax-friedrichs-1d
  (hash
   'name "lax-friedrichs"
   'waves (list
           (let ([flux_u_L `(* 0.0 u_L)]
                 [flux_u_R `(* 0.0 u_R)]
                 [amax `(abs alpha)])
             (list
              (list `(* 0.5 (- (- u_R u_L) (/ (- ,flux_u_R ,flux_u_L) ,amax))))
              (list `(* 0.5 (+ (- u_R u_L) (/ (- ,flux_u_R ,flux_u_L) ,amax))))
              )
             )
           )
   'speeds (list
            (let ([amax `(abs alpha)])
              (list `(- ,amax) amax)))
   )
  )

(define minmod-1d
  (hash
   'name "minmod"
   'order 2
   'left-reconstruction (list
                         (let ([minmod_f `(+ (max 0.0 (min (- f f_L) (- f_R f))) (min 0.0 (max (- f f_L) (- f_R f))))])
                           (list `(- f (* 0.5 ,minmod_f)))))
   'right-reconstruction (list
                          (let ([minmod_f `(+ (max 0.0 (min (- f f_L) (- f_R f))) (min 0.0 (max (- f f_L) (- f_R f))))])
                            (list `(+ f (* 0.5 ,minmod_f)))))
   )
  )

(define ssp-rk3-1d
  (hash
   'name "ssp-rk3"
   'order 3
   'stages (list
            (list
             (list `(+ f0 (* dt f0_rhs)))
             (list `(+ (* 0.75 f0) (* 0.25 (+ f1 (* dt f1_rhs)))))
             (list `(+ (* (/ 1.0 3.0) f0) (* (/ 2.0 3.0) (+ f2 (* dt f2_rhs)))))
             )
            )
   'source-stages (list
                   (list `(+ f0 (* dt f0_rhs)))
                   (list `(+ (* 0.75 f0) (* 0.25 (+ f1 (* dt f1_rhs)))))
                   (list `(+ (* (/ 1.0 3.0) f0) (* (/ 2.0 3.0) (+ f2 (* dt f2_rhs)))))
                   )
   )
  )

(define centered-diffusion-1d
  (hash
   'name "centered-diffusion"
   'interface-state (list
                     (list `(* 0.5 (+ f_Lx f_Rx))))
   'interface-gradients (list
                         (list
                          (list `(/ (- f_Rx f_Lx) (- x_Rx x_Lx)))))
   )
  )
                    