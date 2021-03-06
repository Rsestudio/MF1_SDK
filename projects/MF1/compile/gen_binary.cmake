
execute_process(COMMAND ${CMAKE_C_COMPILER} -print-file-name=crt0.o OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE CRT0_OBJ)
execute_process(COMMAND ${CMAKE_C_COMPILER} -print-file-name=crtbegin.o OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE CRTBEGIN_OBJ)
execute_process(COMMAND ${CMAKE_C_COMPILER} -print-file-name=crtend.o OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE CRTEND_OBJ)
execute_process(COMMAND ${CMAKE_C_COMPILER} -print-file-name=crti.o OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE CRTI_OBJ)
execute_process(COMMAND ${CMAKE_C_COMPILER} -print-file-name=crtn.o OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE CRTN_OBJ)


set(CMAKE_C_LINK_EXECUTABLE "<CMAKE_C_COMPILER> <FLAGS> <CMAKE_C_LINK_FLAGS> \"${CRTI_OBJ}\" \"${CRTBEGIN_OBJ}\" <OBJECTS> \"${CRTEND_OBJ}\" \"${CRTN_OBJ}\" -o <TARGET>.elf -Wl,--start-group -Wl,--whole-archive <LINK_LIBRARIES> -Wl,--no-whole-archive -Wl,--end-group")
set(CMAKE_CXX_LINK_EXECUTABLE "<CMAKE_CXX_COMPILER> <FLAGS> <CMAKE_CXX_LINK_FLAGS> \"${CRTI_OBJ}\" \"${CRTBEGIN_OBJ}\" <OBJECTS> \"${CRTEND_OBJ}\" \"${CRTN_OBJ}\" -o <TARGET>.elf -Wl,--start-group -Wl,--whole-archive <LINK_LIBRARIES> -Wl,--no-whole-archive -Wl,--end-group")


# Config toolchain
if(CONFIG_TOOLCHAIN_PATH)
    set(CMAKE_SIZE   "${CONFIG_TOOLCHAIN_PATH}/${CONFIG_TOOLCHAIN_PREFIX}size${EXT}")
    set(CMAKE_OBJDUMP "${CONFIG_TOOLCHAIN_PATH}/${CONFIG_TOOLCHAIN_PREFIX}objdump${EXT}")
else()
    set(CMAKE_SIZE   "size${EXT}")
    set(CMAKE_SIZE   "objdump${EXT}")
endif()

# add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
#         COMMAND ${CMAKE_OBJCOPY} --output-format=binary ${CMAKE_BINARY_DIR}/${PROJECT_NAME}.elf ${CMAKE_BINARY_DIR}/${PROJECT_NAME}.bin
#         COMMENT "-- Generating .bin firmware at ${CMAKE_BINARY_DIR}/${PROJECT_NAME}.bin"
#         )

# Build target
add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
        # COMMAND ${CMAKE_OBJCOPY} --output-format=binary ${CMAKE_BINARY_DIR}/${PROJECT_NAME}${SUFFIX} --remove-section .iodata ${CMAKE_BINARY_DIR}/${PROJECT_NAME}.bin
        COMMAND ${CMAKE_OBJCOPY} --output-format=binary ${CMAKE_BINARY_DIR}/${PROJECT_NAME}.elf --remove-section .iodata ${CMAKE_BINARY_DIR}/${PROJECT_NAME}.bin
        COMMENT "Generating .bin firmware at ${CMAKE_BINARY_DIR}/${PROJECT_NAME}.bin")
		
add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
        # COMMAND ${CMAKE_OBJCOPY} --output-format=binary ${CMAKE_BINARY_DIR}/${PROJECT_NAME}${SUFFIX} --only-section .iodata ${CMAKE_BINARY_DIR}/${PROJECT_NAME}_iodata.bin
        COMMAND ${CMAKE_OBJCOPY} --output-format=binary ${CMAKE_BINARY_DIR}/${PROJECT_NAME}.elf --only-section .iodata ${CMAKE_BINARY_DIR}/${PROJECT_NAME}_iodata.bin 
        COMMENT "Generating .bin file ...")

add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
        COMMAND ${CMAKE_SIZE} ${CMAKE_BINARY_DIR}/${PROJECT_NAME}.elf
        COMMENT "============= firmware ============="
        )

add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
        COMMAND ${CMAKE_OBJDUMP} -S ${CMAKE_BINARY_DIR}/${PROJECT_NAME}.elf > ${CMAKE_BINARY_DIR}/${PROJECT_NAME}.txt
        )






