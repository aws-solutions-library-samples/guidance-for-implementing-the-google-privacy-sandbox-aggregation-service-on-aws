FROM public.ecr.aws/amazoncorretto/amazoncorretto:22 as build

WORKDIR /workspace/app

COPY mvnw .
RUN chmod +x ./mvnw
COPY .mvn .mvn

COPY pom.xml .
RUN ./mvnw dependency:go-offline

COPY src src

RUN ./mvnw package -DskipTests

FROM public.ecr.aws/amazoncorretto/amazoncorretto:22

ARG JAR_FILE=/workspace/app/target/*.jar
COPY --from=build ${JAR_FILE} app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app.jar"]
