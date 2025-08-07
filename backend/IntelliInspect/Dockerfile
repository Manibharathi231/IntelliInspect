# Stage 1: Build
# Stage 1: Build
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy only the project file and restore
COPY IntelliInspect/IntelliInspect.csproj IntelliInspect/
WORKDIR /src/IntelliInspect
RUN dotnet restore

# Copy the rest of the source
COPY IntelliInspect/. .

# Publish the project
RUN dotnet publish -c Release -o /app/publish

# Stage 2: Runtime
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
WORKDIR /app
COPY --from=build /app/publish .

EXPOSE 80
ENTRYPOINT ["dotnet", "IntelliInspect.dll"]

 