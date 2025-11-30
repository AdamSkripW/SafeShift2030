import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  
  // Get token from localStorage
  const token = localStorage.getItem('authToken');

  // Clone request and add authorization header if token exists
  const clonedRequest = token 
    ? req.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`
        }
      })
    : req;

  // Handle the request and catch errors
  return next(clonedRequest).pipe(
    catchError((error: HttpErrorResponse) => {
      // If we get 401 Unauthorized, the session is invalid
      if (error.status === 401) {
        console.warn('Session invalid or expired - logging out');
        
        // Clear local storage
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        
        // Redirect to login page
        router.navigate(['/start']);
      }
      
      return throwError(() => error);
    })
  );
};
