# Profile: JVM (Java / Kotlin / Scala)

## Detect

- Maven: `pom.xml`, `mvnw`, `mvnw.cmd`, `.mvn/`
- Gradle: `build.gradle(.kts)`, `settings.gradle(.kts)`, `gradlew`, `gradlew.bat`
- Entry: `src/main/java/.../Application.java`, `Main.java`,
  `src/main/kotlin/.../Application.kt`
- Tests: `src/test/java`, `src/test/kotlin`, `src/integrationTest`
- Lint: `checkstyle.xml`, `spotbugs`, `detekt`, `scalafmt`

## Commands to verify

Maven:

```bash
mvn -q -DskipTests compile
mvn -q test
mvn -q test -Dtest=ClassName
```

Gradle:

```bash
./gradlew compileJava
./gradlew test
./gradlew test --tests 'com.example.ClassName'
./gradlew check
```

Use the wrapper if present; never assume a global Maven/Gradle install.

## Common invariants

- Migrations are additive; schema changes ship with a rollback plan.
- Profiles/environments are explicit; no production defaults.
- Secrets come from env/secret manager, not `application.properties`.
- Generated sources are not hand-edited.
- Transactions own their boundaries; no hidden long transactions.
- API changes update the contract/OpenAPI if one exists.

## Hazards

- Integration tests needing a database, broker, or container.
- Gradle/Maven daemon and local caches.
- Multi-module builds; document the focused module command.
- Spring profiles and config precedence.
- Generated code under `build/`/`target/`.

## Docs to generate

- `docs/testing.md`: unit vs integration, containers, test profiles.
- `docs/architecture.md`: modules, layers, data ownership.
- `docs/operations.md`: jar/war artifact, JVM flags, deploy target.
