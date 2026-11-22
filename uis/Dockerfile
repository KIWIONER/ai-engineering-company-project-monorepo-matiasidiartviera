# Usamos una imagen oficial y muy ligera de Node (versión 20, recomendada para Next.js)
FROM node:20-alpine

# Definimos el directorio de trabajo con propiedad para el usuario no-root 'node'
WORKDIR /app
RUN chown node:node /app

# Copiamos SOLO los archivos de dependencias de ambas apps con propietario no-root
COPY --chown=node:node website/package*.json ./website/
COPY --chown=node:node backoffice/package*.json ./backoffice/

# Instalamos las dependencias de ambas aplicaciones por separado como 'node'
USER node
RUN cd website && npm install
RUN cd backoffice && npm install

# Copiamos el resto del código de todas las interfaces y el script start.sh
COPY --chown=node:node . .

# Permisos de ejecución explícitos solo para el propietario/grupo (sin 777)
RUN chmod 750 start.sh

# Exponemos ambos puertos para que se puedan conectar desde tu navegador local
EXPOSE 3000
EXPOSE 3001

# Comando maestro que arranca ambas aplicaciones en paralelo como usuario no-root
CMD ["./start.sh"]