ENTRY(reset_handler)
MEMORY {
    FLASH (rx) : ORIGIN = 0x08004000, LENGTH = 896K
    RAM (rw) : ORIGIN = 0x20001000, LENGTH = 80K
}
SECTIONS {
    .vectors 0x08004000 : { KEEP(*(.vectors)) } > FLASH
    .family 0x08004810 : { BYTE(0x43) BYTE(0x34) BYTE(0x30) BYTE(0x30) } > FLASH
    .activation 0x08004c00 : { LONG(0xffffffff) } > FLASH
    .text 0x08005000 : { *(.text*) *(.rodata*) } > FLASH
    .data : ALIGN(4) { _sdata = .; *(.data*) . = ALIGN(4); _edata = .; } > RAM AT> FLASH
    _sidata = LOADADDR(.data);
    .bss (NOLOAD) : ALIGN(4) { _sbss = .; *(.bss*) *(COMMON) . = ALIGN(4); _ebss = .; } > RAM
    /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.eh_frame*) }
    ASSERT(SIZEOF(.vectors) == 0x400, "Expected 256 vector slots")
    ASSERT(LOADADDR(.data) + SIZEOF(.data) <= 0x080e3fd0, "896 KiB package including 48-byte header")
    ASSERT(_ebss <= 0x20015000, "Preserve at least 8 KiB below SP20017000")
}
