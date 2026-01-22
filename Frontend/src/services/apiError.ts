/**
 * Erreur personnalisée pour les appels API
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public statusText?: string,
    public data?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
    // Maintient la stack trace pour le débogage
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiError);
    }
  }

  /**
   * Vérifie si l'erreur est due à un timeout
   */
  isTimeout(): boolean {
    return this.status === 408;
  }

  /**
   * Vérifie si l'erreur est due à une authentification
   */
  isUnauthorized(): boolean {
    return this.status === 401;
  }

  /**
   * Vérifie si l'erreur est due à une interdiction d'accès
   */
  isForbidden(): boolean {
    return this.status === 403;
  }

  /**
   * Vérifie si l'erreur est due à une ressource non trouvée
   */
  isNotFound(): boolean {
    return this.status === 404;
  }

  /**
   * Vérifie si l'erreur est due à un problème serveur
   */
  isServerError(): boolean {
    return this.status !== undefined && this.status >= 500;
  }

  /**
   * Retourne un message d'erreur utilisateur-friendly
   */
  getUserMessage(): string {
    if (this.isTimeout()) {
      return 'La requête a pris trop de temps. Veuillez réessayer.';
    }
    if (this.isUnauthorized()) {
      return 'Votre session a expiré. Veuillez vous reconnecter.';
    }
    if (this.isForbidden()) {
      return 'Vous n\'avez pas les permissions nécessaires pour cette action.';
    }
    if (this.isNotFound()) {
      return 'La ressource demandée n\'a pas été trouvée.';
    }
    if (this.isServerError()) {
      if (this.status === 502) {
        return 'Le serveur est temporairement indisponible. Veuillez réessayer dans quelques instants.';
      }
      if (this.status === 503) {
        return 'Le service est temporairement indisponible. Veuillez réessayer plus tard.';
      }
      return 'Une erreur serveur s\'est produite. Veuillez réessayer plus tard.';
    }
    
    // Messages spécifiques pour les erreurs 400
    if (this.status === 400) {
      // Si le message contient des détails spécifiques, les utiliser
      if (this.data && typeof this.data === 'object') {
        const data = this.data as Record<string, any>;
        if (data.detail && typeof data.detail === 'string') {
          return data.detail;
        }
      }
      return this.message || 'Requête invalide. Vérifiez les données envoyées.';
    }
    
    // Message par défaut
    return this.message || 'Une erreur s\'est produite. Veuillez réessayer.';
  }

  /**
   * Retourne les détails de l'erreur pour le débogage
   */
  getDebugInfo(): Record<string, unknown> {
    return {
      message: this.message,
      status: this.status,
      statusText: this.statusText,
      data: this.data,
      type: this.name,
    };
  }
}

