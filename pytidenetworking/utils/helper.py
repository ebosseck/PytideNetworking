USHORT_MAX_VALUE = 65535

def getSequenceGap(seqId1: int, seqId2: int) -> int:
    """
    Computes the gap between two sequence IDs

    :param seqId1: first sequence id
    :param seqId2: second sequence id
    :return: the gap between seqId1 and seqID2, accounting for value wrap around
    """
    seqId1 = seqId1 & 0xffff
    seqId2 = seqId2 & 0xffff

    gap = seqId1 - seqId2
    if abs(gap) <= 32768:
        return gap

    return (USHORT_MAX_VALUE + 1 + seqId1 if seqId1 <= 32768 else seqId1) - (USHORT_MAX_VALUE + 1 + seqId2 if seqId2 <= 32768 else seqId2)