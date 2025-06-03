import dagger
from dagger import dag, function, object_type


@object_type
class DaggerCicd:

    @function
    def build(self, source: dagger.Directory) -> dagger.Container:

        return dag.container().from_("maven:latest")\
                .with_mounted_directory("/src", source)\
                .with_workdir("/src")\
                .with_exec(["mvn", "clean", "install", "-DskipTests"])
    @function
    def build_image(self, source: dagger.Directory) -> dagger.DockerBuild:

        return dag.docker().build()
                
    def start_db(self, source: dagger.Directory) -> dagger.Service:

        return dag.container()\
                .from_("postgres:17.5-alpine")\
                .with_env_variable("POSTGRES_USER", "postgres")\
                .with_env_variable("POSTGRES_PASSWORD", "password")\
                .with_exposed_port(5432)\
                .with_mounted_file("/docker-entrypoint-initdb.d/init.sql", dagger.Directory.file(source, "init.sql"))\
                .as_service()

    def start_app(self, db: dagger.Service,source: dagger.Directory) -> dagger.Service:
        
        return dag.container().from_("maven:latest")\
                .with_mounted_directory("/src", source)\
                .with_workdir("/src")\
                .with_service_binding("database", db)\
                .with_exposed_port(8080)\
                .as_service(args=["mvn", "spring-boot:run"])
                
    @function
    def run(self, source: dagger.Directory) -> dagger.Container :
        
        db = self.start_db(source)
        app = self.start_app(db, source)
        
        return dag.container().from_("alpine:latest")\
                .with_exec(["apk", "--no-cache", "add", "curl"])\
                .with_service_binding("database",db)\
                .with_service_binding("app",app)\
                .terminal()