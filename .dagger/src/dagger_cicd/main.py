import dagger
from dagger import dag, function, object_type


@object_type
class DaggerCicd:

    @function
    def build(self, source: dagger.Directory) -> dagger.Container:

        return dag.container().from_("maven:latest")\
                .with_mounted_directory("/src", source)\
                .with_workdir("/src")\
                .with_exec(["mvn", "clean", "install", "-DskipTests
                            "])

    @function
    def start_db(self, source_sql: dagger.File) -> dagger.Service:

        return dag.container()\
                .from_("postgres:17.5-alpine")\
                .with_env_variable("POSTGRES_USER", "postgres")\
                .with_env_variable("POSTGRES_PASSWORD", "password")\
                .with_exposed_port(5432)\
                .with_mounted_file("/docker-entrypoint-initdb.d/init.sql", source_sql)\
                .as_service(use_entrypoint=True)

    @function
    async def run(self, source_code: dagger.Directory, source_sql: dagger.File) -> str:

        db_service : dagger.Service = self.start_db(source_sql)

        return await (dag.container().from_("maven:latest")\
                .with_mounted_directory("/src", source_code)\
                .with_workdir("/src")\
                .with_service_binding("database", db_service)\
                .with_exposed_port(8080)\
                .with_exec(["mvn", "spring-boot:run"]).stdout())